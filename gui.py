import tkinter as tk
from tkinter import filedialog, messagebox

from pathlib import Path

import amulet

from wooldrive import list_files, store

import threading

world_path = None

root = tk.Tk()
root.title("Wool Drive")
root.geometry("500x400")

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
    file_list.delete(0, tk.END)
    level = amulet.load_level(world_path)
    files = list_files(level)
    level.close()
    for name, size, wall in files:
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
    threading.Thread(target=store_thread, args=(file_path,), daemon=True).start()

def store_thread(file_path):
    try:
        store(file_path, world_path)
        root.after(0, store_done, None)
    except Exception as e:
        root.after(0, store_done, e)

def store_done(error):
    store_button.config(state="normal")
    if error:
        messagebox.showerror("Wool Drive", str(error))
    refresh_files()


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

root.columnconfigure(0, weight=1)
root.rowconfigure(2, weight=1)

if world_path and Path(world_path).exists():
    world_path_label.config(text=Path(world_path).name)
    refresh_files()

root.mainloop()