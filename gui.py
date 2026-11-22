import tkinter as tk
from tkinter import filedialog, messagebox
import hashlib
from decoder import read_wall

from pathlib import Path

import amulet

import threading

from PIL import Image, ImageTk
from wooldrive import list_files, store, pack, to_nibbles, to_colours, width, height, per_wall

wool_rgb = {
    "white": (233, 236, 236), "orange": (240, 118, 19),
    "magenta": (189, 68, 179), "light_blue": (58, 175, 217),
    "yellow": (248, 197, 39), "lime": (112, 185, 25),
    "pink": (237, 141, 172), "gray": (62, 68, 71),
    "light_gray": (142, 142, 134), "cyan": (21, 137, 145),
    "purple": (121, 42, 172), "blue": (53, 57, 157),
    "brown": (114, 71, 40), "green": (84, 109, 27),
    "red": (160, 39, 34), "black": (20, 21, 25),
}
empty_rgb = (90, 125, 60)

world_path = None
files = []

root = tk.Tk()
root.title("Wool Drive")
root.geometry("570x450")

try:
    with open("defaultworldpath.txt") as f:
        world_path = f.read()
except FileNotFoundError:
    print("INFO: defaultworldpath.txt file does not exist, it will be created when choosing a world")

def choose_world():
    global world_path
    folder = filedialog.askdirectory(title="Choose a Minecraft world folder")
    if folder:
        world_path = folder
        world_path_label.config(text=Path(folder).name)
        with open("defaultworldpath.txt", "w") as f:
            f.write(folder)
        refresh_files()

def refresh_files():
    global files
    file_list.delete(0, tk.END)
    level = amulet.load_level(world_path)
    files = list_files(level)
    level.close()
    for name, size, wall, _ in files:
        file_list.insert(tk.END, f"{name}   ({size} bytes, wall {wall})")
    count_label.config(text=f"{len(files)} file(s) stored")

def store_file():
    if world_path is None:
        messagebox.showerror("Wool Drive", "ERROR: Choose a world first before attempting to store a file")
        return
    file_path = filedialog.askopenfilename(title="Choose a file to store")
    if not file_path:
        return

    store_button.config(state="disabled")
    count_label.config(text=f"Storing {Path(file_path).name}...")
    compress = compress_var.get()
    protect = protect_var.get()
    threading.Thread(target=store_thread, args=(file_path, compress, protect), daemon=True).start()

def store_thread(file_path, compress, protect):
    try:
        store(file_path, world_path, compress, protect)
        root.after(0, store_done, None)
    except Exception as e:
        root.after(0, store_done, e)

def store_done(error):
    store_button.config(state="normal")
    if error:
        messagebox.showerror("Wool Drive", str(error))
    refresh_files()

def recover_files():
    selected = file_list.curselection()
    if not selected:
        messagebox.showerror("Wool Drive", "ERROR: Select a file in the list first")
        return
    name = files[selected[0]][0]

    save_path = filedialog.asksaveasfilename(title="Save recovered file as")
    if not save_path:
        return

    recover_button.config(state="disabled")
    count_label.config(text=f"Recovering {name}...")
    threading.Thread(target=recover_thread, args=(name, save_path), daemon=True).start()

def recover_thread(name, save_path):
    try:
        _, data = read_wall(world_path, name)
        Path(save_path).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        root.after(0, recover_done, None, f"Recovered {name}\n\nSHA-256:\n{digest}")
    except Exception as e:
        root.after(0, recover_done, e, None)

def recover_done(error, message):
    recover_button.config(state="normal")
    if error:
        messagebox.showerror("Wool Drive", str(error))
    else:
        messagebox.showinfo("Wool Drive", message)
    count_label.config(text=f"{len(files)} file(s) stored")

def preview_file():
    file_path = filedialog.askopenfilename(title="Choose a file to preview")
    if not file_path:
        return

    path = Path(file_path)
    wall = to_colours(to_nibbles(pack(path.name, path.read_bytes(), compress_var.get(), protect_var.get())))
    walls_used = (len(wall) + per_wall - 1) // per_wall

    first = wall[:per_wall]
    pixels = [wool_rgb[c] for c in first] + [empty_rgb] * (per_wall - len(first))

    img = Image.new("RGB", (width, height))
    img.putdata(pixels)
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    img = img.resize((width * 3, height * 3), Image.NEAREST)

    win = tk.Toplevel(root)
    win.title(f"Preview: {path.name}")
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(win, image=photo)
    label.image = photo
    label.grid(row=0, column=0)
    wall_label = tk.Label(win, text=f"Wall 1 of {walls_used}   ({len(wall)} blocks")
    wall_label.grid(row=1, column=0, pady=5)


choose_world_button = tk.Button(root, text="Choose world", command=choose_world)
choose_world_button.grid(row=0, column=0, pady=5)

world_path_label = tk.Label(root, text="None Selected")
world_path_label.grid(row=0, column=1, padx=5, pady=5)

count_label = tk.Label(root, text="0 file(s) stored")
count_label.grid(row=1, column=0, padx=5, pady=5)

file_list = tk.Listbox(root)
file_list.grid(row=2, column=0, columnspan=2, sticky="nsew")

store_button = tk.Button(root, text="Store file", command=store_file)
store_button.grid(row=1, column=1, sticky="w", padx=5, pady=5)

recover_button = tk.Button(root, text="Recover file", command=recover_files)
recover_button.grid(row=3, column=0, columnspan=2, pady=5)

preview_button = tk.Button(root, text="Preview file", command=preview_file)
preview_button.grid(row=1, column=0, padx=5, pady=5, sticky="e")

compress_var = tk.BooleanVar(value=True)
compress_check = tk.Checkbutton(root, text="Compress (only if it makes the file smaller)", variable=compress_var)
compress_check.grid(row=4, column=0, columnspan=2, pady=5)

protect_var = tk.BooleanVar(value=False)
protect_check = tk.Checkbutton(root, text="Error Correction (14% Bigger)", variable=protect_var)
protect_check.grid(row=5, column=0, columnspan=2, pady=5)

root.columnconfigure(0, weight=1)
root.rowconfigure(2, weight=1)

if world_path and Path(world_path).exists():
    world_path_label.config(text=Path(world_path).name)
    refresh_files()

root.mainloop()