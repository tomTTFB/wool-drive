import hashlib
import sys

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
        high, low = nibbles[i], nibbles[i + 1]
        output.append((high << 4) | low)
    return bytes(output)

if __name__ == "__main__":
    path = sys.argv[1]
    data = open(path, "rb").read()

    nibs = to_nibbles(data)
    back = from_nibbles(nibs)

    assert len(nibs) == len(data * 2)
    assert all(0 <= n <= 15 for n in nibs)

    print("Before: " + hashlib.sha256(data).hexdigest())
    print("After: " + hashlib.sha256(back).hexdigest())

    matches = False
    if data == back:
        print("Matches?: True")
    else:
        print("Matches?: False")