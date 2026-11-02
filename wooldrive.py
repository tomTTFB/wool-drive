import struct
import sys
from pathlib import Path

# Wool SToRage
signature = b"WSTR"

colours = [
    "white", "orange", "magenta", "light_blue",
    "yellow", "lime", "pink", "gray",
    "light_gray", "cyan", "purple", "blue",
    "brown", "green", "red", "black",
]

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

blob = pack("test.txt", b"hello")
wall = to_colours(to_nibbles(blob))
print(wall[:8])

back = from_nibbles(from_colours(wall))
print(unpack(back))