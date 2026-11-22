import amulet
import hashlib
import struct
import sys
from pathlib import Path

from wooldrive import *

def read_wall(world_path: str, wanted: str) -> tuple[str, bytes]:
    level = amulet.load_level(world_path)
    for name, size, wall, total_bytes in list_files(level):
        if name == wanted:
            names = read_blocks(level, wall * per_wall, total_bytes * 2)
            level.close()
            blob, erased = block_to_bytes(names)
            return unpack(blob, erased)
    level.close()
    raise FileNotFoundError(f"ERROR: {wanted} is not stored in this world")

def recover(world_path: str, wanted: str, out_dir: str = "recovered") -> None:
    name, data = read_wall(world_path, wanted)
    out = Path(out_dir) / name
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    print(f"Recovered {name}: {len(data)} bytes")
    
if __name__ == "__main__":
    recover(sys.argv[1], sys.argv[2])