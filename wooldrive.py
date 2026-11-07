import struct
import sys
from pathlib import Path
import amulet
from amulet.api.block import Block

# Wool SToRage
signature = b"WSTR"

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

def pack(name: str, data: bytes) -> bytes:
    name_bytes = name.encode("utf-8")
    lengths = struct.pack(">BI", len(name_bytes), len(data))
    return signature + lengths + name_bytes + data

def unpack(blob: bytes) -> tuple[str, bytes]:
    if blob[:4] != signature:
        raise ValueError("ERROR: file not a Wool Drive file")

    name_len, data_len = struct.unpack(">BI", blob[4:9])
    name_start = 9
    data_start = name_start + name_len

    name = blob[name_start:data_start].decode("utf-8")
    data = blob[data_start:data_start + data_len]
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

def read_header(level, wall: int):
    start = wall * per_wall
    names = read_blocks(level, start, 18)
    if any(n not in colour_index for n in names):
        return None

    head = from_nibbles(from_colours(names))
    if head[:4] != signature:
        return None
    name_len, data_len = struct.unpack(">BI", head[4:9])

    name_names = read_blocks(level, start + 18, name_len * 2)
    name = from_nibbles(from_colours(name_names)).decode("utf-8")

    total_blocks = (9 + name_len + data_len) * 2
    walls_used = (total_blocks + per_wall - 1) // per_wall
    return name, data_len, walls_used

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
        name, data_len, walls_used = header
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

def store(file_path: str, world_path: str) -> None:
    path = Path(file_path)
    blob = pack(path.name, path.read_bytes())
    wall = to_colours(to_nibbles(blob))

    level = amulet.load_level(world_path)
    start_wall = find_free_wall(level)
    level.close()

    write_wall(world_path, wall, start_wall)
    verify_wall(world_path, wall, start_wall)
    print("Done")

def position(i:int) -> tuple[int, int, int]:
    wall = i // per_wall
    spot = i % per_wall
    x = spot % width
    y = base_y + spot // width
    z = wall * wall_gap
    return x, y, z

if __name__ == "__main__":
    store(sys.argv[1], sys.argv[2])