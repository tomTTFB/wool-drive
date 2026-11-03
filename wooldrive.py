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

def pack(name: str, data: bytes) -> bytes:
    name_bytes = name.encode("utf-8")
    lengths = struct.pack(">BI", len(name_bytes), len(data))
    return signature + lengths + name_bytes + data

def unpack(blob: bytes) -> tuple[str, bytes]:
    if blob[:4] != signature:
        print("ERROR: file not a Wool Drive file")

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
        print(f"ERROR: Odd number of nibbles!")
    output = bytearray()
    for i in range(0, len(nibbles), 2):
        output.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(output)

colour_index = {name: i for i, name in enumerate(colours)}

def to_colours(nibbles: list[int]) -> list[str]:
    return [colours[n] for n in nibbles]

def from_colours(names: list[str]) -> list[int]:
    return [colour_index[name] for name in names]

def write_wall(world_path: str, wall: list[str]) -> None:
    blocks = {name: Block("minecraft", f"{name}_wool") for name in colours}

    level = amulet.load_level(world_path)
    for i, name in enumerate(wall):
        x, y, z = position(i)
        level.set_version_block(x, y, z, dimension, version, blocks[name])
    level.save()
    level.close()

def store(file_path: str, world_path: str) -> None:
    path = Path(file_path)
    blob = pack(path.name, path.read_bytes())
    wall = to_colours(to_nibbles(blob))

    write_wall(world_path, wall)
    print("Done")

def position(i:int) -> tuple[int, int, int]:
    per_wall = width * height
    wall = i // per_wall
    spot = i % per_wall
    x = spot % width
    y = base_y + spot // width
    z = wall * wall_gap
    return x, y, z

if __name__ == "__main__":
    store(sys.argv[1], sys.argv[2])