# Wool Drive

Wool Drive is a python app that uses amulet to store any file inside a real Minecraft world as walls of coloured wool, then reads the world back and gives you the same file.

## Description

Wool Drive is a Python app that hides files in a Minecraft Java world. Every byte of a file is split into two nibbles (4 bits each, 0 to 15), and each nibble becomes one of Minecraft's 16 wool colours, so every byte takes 2 blocks. The blocks are laid out in 128 × 128 walls, with a waxed sign beside each one showing the file name, size and which part of the file it is. The world still opens in Minecraft, and you can walk around your data.

Before the file, Wool Drive writes a small header:

| Bytes | Info | Extra Info |
|---|---|---|
| 4 | `WSTR` | Magic value ("Wool SToRage") so Wool Drive knows the wall is a file |
| 1 | Filename length | Names up to 255 bytes |
| 4 | File size | in Big-endian, files up to about 4 GB |
| n | Filename | UTF-8 |
|  | File data | |

The colour for each nibble:

| Nibble | Wool | Nibble | Wool |
|---|---|---|---|
| 0 | White | 8 | Light Gray |
| 1 | Orange | 9 | Cyan |
| 2 | Magenta | 10 | Purple |
| 3 | Light Blue | 11 | Blue |
| 4 | Yellow | 12 | Brown |
| 5 | Lime | 13 | Green |
| 6 | Pink | 14 | Red |
| 7 | Gray | 15 | Black |

**How much fits:** Each wall is 128 × 128 blocks = 16,384 blocks, and every byte takes 2 blocks, so one wall holds about 8 KB.

**Every write is checked.** After storing a file, the app reopens the world from disk and reads every block back and if even one block doesn't match, it stops with an error saying where.

**Proof it round trips.** These files are stored in the demo world, and the SHA-256 of each original matches the file recovered from the world:

| File | Size | SHA-256 (before and after) |
|---|---|---|
| a.txt | 32 bytes | `da665309a7949e794b726c42230d34fbbd72a777cb560d462218c1f09fccb5df` |
| b.txt | 43 bytes | `ba66c928fccb1f666a24d12e813ba82770f729d9c08e2be29be15923e518e3bf` |
| sigma.png | 194,620 bytes | `1edb68848a32616854c70f86aa9a9cccf4b8dff1020ffa2b2b245a2be700cd59` |
| test.zip | 194,145 bytes | `979fdd002704eeae11084101db510c42586fc13f69c8e369a08f43b87b433442` |

### Screenshots

![Wool walls with signs](images/walls.png)

![The Wool Drive app](images/gui.png)

## Getting Started

### Dependencies

* To run the release build: None
* To open the world in game: Minecraft Java Edition (tested on 26.1 but Amulet supports any version 1.12.2 and up)
* To run from source: Python 3.12, plus `amulet-core` and `pillow`

### Installing

* Download the latest build and `wool-drive-demo-world.zip` from the [Releases](../../releases) page
* Unzip the demo world anywhere. It already has four files stored in it: two text files, a PNG and a zip

To run from source instead:

```
git clone https://github.com/tomTTFB/wool-drive.git
cd wool-drive
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install amulet-core pillow
```

### Executing program

* Make sure the world you choose isn't open ingame
* Run Wool Drive (or `python3 gui.py` from source)
* Click **Choose world** and pick the world you want
* Select a file in the list and click **Recover file**, then choose where to save it
* Compare the SHA-256 in the popup with the table above
* To store your own file, click **Store file** and pick any file
* To see what a file will look like as wool first, click **Preview file**

Wool Drive can also be used with the CLI:

```
python3 wooldrive.py store <file> <world folder>
python3 wooldrive.py list <world folder>
python3 decoder.py <world folder> <file name>
```

## Help

**The walls look pitch black on top**: Amulet doesn't recalculate Minecrafts lighting, so new walls can look dark. Try placing or breaking blocks around the walls to force a lighting update

To check a recovered file yourself:

```
sha256sum <file>                 # Linux
shasum -a 256 <file>             # macOS
Get-FileHash <file>              # Windows PowerShell
```

## License

MIT