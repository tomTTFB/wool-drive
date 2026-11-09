import amulet
import hashlib
import struct
import sys
from pathlib import Path

from wooldrive import per_wall, read_blocks, list_files, from_colours, from_nibbles, unpack

def read_wall(world_path: str, wanted: str) -> tuple[str, bytes]:
    level = amulet.load_level(world_path)
    for name,size,wall, in list_files(level):
        if name == wanted:
            total_bytes = 9 + len(name.encode("utf-8")) + size
            names = read_blocks(level, wall * per_wall, total_bytes * 2)
            level.close()
            return unpack(from_nibbles(from_colours(names)))
    level.close()
    raise FileNotFoundError(f"{wanted} is not stored in this world")

def recover(world_path: str, wanted: str, out_dir: str = "recovered") -> None:
    name, data = read_wall(world_path, wanted)
    out = Path(out_dir) / name
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    print(f"Recovered {name}: {len(data)} bytes")
    
if __name__ == "__main__":
    recover(sys.argv[1], sys.argv[2])