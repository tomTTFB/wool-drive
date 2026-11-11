import tkinter as tk
from tkinter import filedialog

from pathlib import Path

import amulet

from wooldrive import list_files

world_path = None

root = tk.Tk()
root.title("Wool Drive")
root.geometry("500x400")

def choose_world():
    global world_path
    folder = filedialog.askdirectory(title="Choose a Minecraft world folder")
    if folder:
        world_path = folder
        world_path_label.config(text=Path(folder).name)
        refresh_files()

def refresh_files():
    file_list.delete(0, tk.END)
    level = amulet.load_level(world_path)
    files = list_files(level)
    level.close()
    for name, size, wall in files:
        file_list.insert(tk.END, f"{name}   ({size} bytes, wall {wall})")
    count_label.config(text=f"{len(files)} file(s) stored")

choose_world_button = tk.Button(root, text="Choose world", command=choose_world)
choose_world_button.grid(row=0, column=0, pady=5)

world_path_label = tk.Label(root, text="None Selected")
world_path_label.grid(row=0, column=1, padx=5, pady=5)

count_label = tk.Label(root, text="0 file(s) stored")
count_label.grid(row=1, column=0, padx=5, pady=5)

file_list = tk.Listbox(root)
file_list.grid(row=2, column=0, columnspan=2, sticky="nsew")

root.columnconfigure(0, weight=1)
root.rowconfigure(2, weight=1)

root.mainloop()