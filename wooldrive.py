import struct
import sys
from pathlib import Path
import amulet
import json
import zlib
from reedsolo import RSCodec, ReedSolomonError

from amulet.api.block import Block
from amulet.api.block_entity import BlockEntity
from amulet_nbt import CompoundTag, ListTag, StringTag, ByteTag, NamedTag

# Wool SToRage
signature = b"WSTR"

# Wool STorage 2
signature_v2 = b"WST2"

colours = [
    "white", "orange", "magenta", "light_blue",
    "yellow", "lime", "pink", "gray",
    "light_gray", "cyan", "purple", "blue",
    "brown", "green", "red", "black",
]

version = ("java", (1, 20, 4))
dimension = "minecraft:overworld"
width = 128
height = 128
base_y = -60
wall_gap = 3
per_wall = width * height

compressed = 1

rs = 2
rs_parity = 32
rs_data = 255 - rs_parity
rsc = RSCodec(rs_parity)

def pack(name: str, data: bytes, compress: bool = True, protect: bool = True) -> bytes:
    name_bytes = name.encode("utf-8")
    flags = 0
    stored = data
    if compress:
        squashed = zlib.compress(data, 9)
        if len(squashed) < len(data):
            stored = squashed
            flags |= compressed
    if protect:
        flags |= rs
    header = signature_v2 + struct.pack(">BBII", flags, len(name_bytes), len(data), len(stored))

    if not protect:
        return header + name_bytes + stored

    if len(name_bytes) > rs_data:
        raise ValueError("ERROR: file name is too long for error correction (max is 223 bytes)")
    return bytes(rsc.encode(header)) + bytes(rsc.encode(name_bytes)) + interleave(rs_encode(stored))

def parse_header(head: bytes):
    if head[:4] == signature_v2:
        flags, name_len, original, stored = struct.unpack(">BBII", head[4:14])
        return 14, flags, name_len, original, stored
    if head[:4] == signature:
        name_len, size = struct.unpack(">BI", head[4:9])
        return 9, 0, name_len, size, size
    return None

def decode_header(blob: bytes, erased: set[int]):
    if not any(p < 14 for p in erased):
        info = parse_header(blob[:14])
        if info and not info[1] & rs:
            return info, info[0]
        if info:
            return info, 46

    head_erase = [p for p in range(46) if p in erased]
    try:
        fixed, _, _ = rsc.decode(blob[:46], erase_pos=head_erase if head_erase else None)
    except ReedSolomonError:
        return None, 0
    info = parse_header(bytes(fixed))
    if info and info[1] & rs:
        return info, 46
    return None, 0

def unpack(blob: bytes, erased: set[int] = frozenset()) -> tuple[str, bytes]:
    info, start = decode_header(blob, erased)
    if info is None:
        raise ValueError("ERROR: not a Wool Drive file, or the header is too damaged")
    header_len, flags, name_len, original, stored = info

    if flags & rs:
        name_end = start + name_len + rs_parity
        name_erase = [p - start for p in erased if start <= p < name_end]
        name_fixed, _, _ = rsc.decode(blob[start:name_end], erase_pos=name_erase if name_erase else None)
        name = bytes(name_fixed).decode("utf-8")

        codeword_count = -(-stored // rs_data)
        data_end = name_end + codeword_count * 255
        data_erased = {p - name_end for p in erased if name_end <= p < data_end}
        data = rs_decode(blob[name_end:data_end], data_erased, stored)
    else:
        if erased:
            raise ValueError("this file is damaged and wasn't stored TNT-proof")
        name = blob[start:start + name_len].decode("utf-8")
        data = blob[start + name_len:start + name_len + stored]

    if flags & compressed:
        data = zlib.decompress(data)
    if len(data) != original:
        raise ValueError("recovered size doesn't match the header")
    return name, data

def to_nibbles(data: bytes) -> list[int]:
    nibbles = []
    for b in data:
        nibbles.append(b >> 4)
        nibbles.append(b & 0x0F)
    return nibbles

def from_nibbles(nibbles: list[int]) -> bytes:
    if len(nibbles) % 2 != 0:
        raise ValueError(f"ERROR: Odd number of nibbles!")
    output = bytearray()
    for i in range(0, len(nibbles), 2):
        output.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(output)

def read_blocks(level, start: int, count:int) -> list[str]:
    names = []
    for i in range(start, start + count):
        x, y, z = position(i)
        block, _ = level.get_version_block(x, y, z, dimension, version)
        names.append(block.base_name.removesuffix("_wool"))
    return names

def block_to_bytes(names: list[str]) -> tuple[bytes, set[int]]:
    out = bytearray()
    erased = set()
    for p in range(0, len(names), 2):
        high, low = names[p], names[p + 1]
        if high in colour_index and low in colour_index:
            out.append((colour_index[high] << 4) | colour_index[low])
        else:
            out.append(0)
            erased.add(p // 2)
    return bytes(out), erased

def read_header(level, wall: int):
    start = wall * per_wall
    head_blocks = read_blocks(level, start, 92)
    if all(n == "air" for n in head_blocks):
        return None

    head, erased = block_to_bytes(head_blocks)
    info, body_start = decode_header(head, erased)
    if info is None:
        raise ValueError(f"ERROR: wall {wall} has blocks on it but no readable Wool Drive header")
    header_len, flags, name_len, original, stored = info

    protected = flags & rs
    name_size = name_len + rs_parity if protected else name_len
    name_blocks = read_blocks(level, start + body_start * 2, name_size * 2)
    name_raw, name_erased = block_to_bytes(name_blocks)

    if protected:
        fixed, _, _ = rsc.decode(name_raw, erase_pos=sorted(name_erased) if name_erased else None)
        name = bytes(fixed).decode("utf-8")
        total_bytes = body_start + name_size + -(-stored // rs_data) * 255
    else:
        if name_erased:
            raise ValueError(f"ERROR: the file name on wall {wall} is damaged")
        name = name_raw.decode("utf-8")
        total_bytes = body_start + name_size + stored

    walls_used = (total_bytes * 2 + per_wall - 1) // per_wall
    return name, original, walls_used, total_bytes

def verify_wall(world_path: str, wall: list[str], start_wall: int) -> None:
    offset = start_wall * per_wall
    level = amulet.load_level(world_path)
    found = read_blocks(level, offset, len(wall))
    level.close()

    bad = [i for i in range(len(wall)) if found[i] != wall[i]]
    if bad is True:
        first = bad[0]
        raise RuntimeError(
            f"verify failed: {len(bad)} of {len(wall)} blocks wrong, "
            f"first at block {first} {position(first)}: "
            f"expected {wall[first]}, found {found[first]}"
        )

def find_free_wall(level) -> int:
    wall = 0
    while True:
        header = read_header(level, wall)
        if header is None:
            return wall
        name, data_len, walls_used, total = header
        wall += walls_used

def list_files(level) -> list[tuple[str, int, int, int]]:
    files = []
    wall = 0
    while True:
        header = read_header(level, wall)
        if header is None:
            return files
        name, data_len, walls_used, total = header
        files.append((name, data_len, wall, total))
        wall += walls_used

colour_index = {name: i for i, name in enumerate(colours)}

def to_colours(nibbles: list[int]) -> list[str]:
    return [colours[n] for n in nibbles]

def from_colours(names: list[str]) -> list[int]:
    return [colour_index[name] for name in names]

def write_wall(world_path: str, wall: list[str], start_wall: int) -> None:
    blocks = {name: Block("minecraft", f"{name}_wool") for name in colours}
    offset = start_wall * per_wall

    level = amulet.load_level(world_path)
    for i, name in enumerate(wall):
        x, y, z = position(offset + i)
        level.set_version_block(x, y, z, dimension, version, blocks[name])
    level.save()
    level.close()

def sign_side(lines: list[str]) -> CompoundTag:
    return CompoundTag({
        "messages": ListTag([StringTag(json.dumps({"text": l})) for l in lines]),
        "color": StringTag("black"),
        "has_glowing_text": ByteTag(0),
    })

def place_signs(world_path: str, name: str, size: int, start_wall: int, walls_used: int) -> None:
    short = name if len(name) <= 15 else name[:14] + "~"
    sign = Block("minecraft", "oak_sign", {"rotation": StringTag("4")})

    level = amulet.load_level(world_path)
    for part in range(walls_used):
        wall = start_wall + part
        x, y, z = -1, base_y, wall * wall_gap
        lines = ["Wool Drive", short, f"{size} bytes", f"part {part + 1}/{walls_used}"]
        nbt = NamedTag(CompoundTag({
            "front_text": sign_side(lines),
            "back_text": sign_side(["", "", "", ""]),
            "is_waxed": ByteTag(1),
        }))
        entity = BlockEntity("minecraft", "sign", x, y, z, nbt)
        level.set_version_block(x, y, z, dimension, version, sign, entity)
    level.save()
    level.close()

def store(file_path: str, world_path: str, compress: bool = True, protect: bool = False) -> None:
    path = Path(file_path)
    data = path.read_bytes()
    blob = pack(path.name, data, compress, protect)

    level = amulet.load_level(world_path)
    start_wall = find_free_wall(level)
    level.close()

    write_wall(world_path, wall, start_wall)
    verify_wall(world_path, wall, start_wall)
    walls_used = (len(wall) + per_wall - 1) // per_wall
    place_signs(world_path, path.name, len(blob) - 9 - len(path.name.encode("utf-8")), start_wall, walls_used)
    print("Done")

def position(i:int) -> tuple[int, int, int]:
    wall = i // per_wall
    spot = i % per_wall
    x = spot % width
    y = base_y + spot // width
    z = wall * wall_gap
    return x, y, z

def rs_encode(payload: bytes) -> list[bytes]:
    padded = payload + bytes(-len(payload) % rs_data)
    return [bytes(rsc.encode(padded[i:i + rs_data])) for i in range(0, len(padded), rs_data)]

def interleave(codewords: list[bytes]) -> bytes:
    return bytes(cw[byte_index] for byte_index in range(255) for cw in codewords)

def rs_decode(stream: bytes, erased: set[int], payload_len: int) -> bytes:
    codeword_count = len(stream) // 255
    out = bytearray()
    for i in range(codeword_count):
        cw = bytes(stream[j * codeword_count + i] for j in range(255))
        erase = [byte_index for byte_index in range(255) if byte_index * codeword_count + i in erased]
        fixed, _, _ = rsc.decode(cw, erase_pos=erase if erase else None)
        out += fixed
    return bytes(out[:payload_len])

if __name__ == "__main__":
    command = sys.argv[1]

    if command == "store":
        store(sys.argv[2], sys.argv[3])
    elif command == "list":
        level = amulet.load_level(sys.argv[2])
        files = list_files(level)
        level.close()
        if not files:
            print("No files stored")
        for name, size, wall in files:
            print(f"wall {wall:>3}  {size:>8} bytes  {name}")
    else:
        print("usage: wooldrive.py store <file> <world> | list <world>")