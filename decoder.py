import amulet
import hashlib
import struct
import sys
from pathlib import Path

from wooldrive import signature, dimension, version, position, from_colours, from_nibbles, unpack

def read_blocks(level, start: int, count:int) -> list[str]:
    names = []
    for i in range(start, start + count):
        x, y, z = position(i)
        block, _ = level.get_version_block(x, y, z, dimension, version)
        names.append(block.base_name.removesuffix("_wool"))
    return names

def read_wall(world_path: str) -> tuple[str, bytes]:
    level = amulet.load_level(world_path)

    head = from_nibbles(from_colours(read_blocks(level, 0 , 18)))
    if head[:4] != signature:
        level.close()
        raise ValueError("ERROR: No Wool Drive file found in this world")
    name_len, data_len = struct.unpack(">BI", head[4:9])

    total_bytes = 9 + name_len + data_len
    names = read_blocks(level, 0, total_bytes * 2)
    level.close

    return unpack(from_nibbles(from_colours(names)))

def recover(world_path: str, out_dir: str = "recovered") -> None:
    name, data = read_wall(world_path)
    out = Path(out_dir) / name
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    print(f"Recovered {name}: {len(data)} bytes")
    
if __name__ == "__main__":
    recover(sys.argv[1])