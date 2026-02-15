import os
import shutil
import logging
import sys
import json
import time
from tkinter import Tk, Button, Label, filedialog, messagebox, PhotoImage
from tkinter.ttk import Progressbar, Style

# ---------------- PATH SETUP ---------------- #

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "file_organizer.log")
FILE_TYPES_FILE = os.path.join(BASE_DIR, "file_types.json")

# ---------------- LOGGING ---------------- #

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# ---------------- FILE TYPES ---------------- #

DEFAULT_FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif"],
    "Documents": [".doc", ".docx", ".txt"],
    "PDF": [".pdf"],
    "Videos": [".mp4", ".avi", ".mkv"],
    "Audio": [".mp3", ".wav"],
    "Archives": [".zip", ".rar"]
}

if not os.path.exists(FILE_TYPES_FILE):
    with open(FILE_TYPES_FILE, "w") as f:
        json.dump(DEFAULT_FILE_TYPES, f, indent=4)

with open(FILE_TYPES_FILE, "r") as f:
    FILE_TYPES = json.load(f)

# ---------------- GLOBALS ---------------- #

selected_folder = ""
last_operations = []

# ---------------- SPLASH ---------------- #

def show_splash():
    splash = Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#1e1e1e")

    w, h = 360, 220
    x = (splash.winfo_screenwidth() - w) // 2
    y = (splash.winfo_screenheight() - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    Label(splash, text="Sortify",
          font=("Segoe UI", 24, "bold"),
          fg="#4FC3F7", bg="#1e1e1e").pack(pady=(50, 5))

    Label(splash, text="Smart File Organizer",
          font=("Segoe UI", 11),
          fg="#bbbbbb", bg="#1e1e1e").pack()

    Label(splash, text="Loading...",
          font=("Segoe UI", 9),
          fg="#888888", bg="#1e1e1e").pack(pady=25)

    splash.update()
    time.sleep(2)
    splash.destroy()

# ---------------- FUNCTIONS ---------------- #

def choose_folder():
    global selected_folder
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        status_label.config(text=f"📁 {selected_folder}")

def organize_files(preview=False):
    global last_operations
    last_operations = []

    if not selected_folder:
        messagebox.showwarning("Sortify", "Please select a folder first!")
        return

    files = [
        f for f in os.listdir(selected_folder)
        if os.path.isfile(os.path.join(selected_folder, f))
        and not f.endswith(".log")
    ]

    if not files:
        messagebox.showinfo("Sortify", "No files to organize.")
        return

    progress["maximum"] = len(files)
    progress["value"] = 0
    percent_label.config(text="0%")

    for i, filename in enumerate(files, start=1):
        src = os.path.join(selected_folder, filename)
        ext = os.path.splitext(filename)[1].lower()
        moved = False

        for folder, extensions in FILE_TYPES.items():
            if ext in extensions:
                dest_folder = os.path.join(selected_folder, folder)
                os.makedirs(dest_folder, exist_ok=True)

                if not preview:
                    shutil.move(src, os.path.join(dest_folder, filename))

                last_operations.append((src, dest_folder))
                logging.info(f"{'PREVIEW' if preview else 'MOVED'} {filename} → {folder}")
                moved = True
                break

        if not moved:
            other = os.path.join(selected_folder, "Others")
            os.makedirs(other, exist_ok=True)

            if not preview:
                shutil.move(src, os.path.join(other, filename))

            last_operations.append((src, other))
            logging.info(f"{'PREVIEW' if preview else 'MOVED'} {filename} → Others")

        progress["value"] = i
        percent_label.config(text=f"{int((i / len(files)) * 100)}%")
        root.update_idletasks()

    messagebox.showinfo(
        "Sortify",
        "Preview completed!" if preview else "Files organized successfully!"
    )

def undo_last():
    if not last_operations:
        messagebox.showinfo("Sortify", "Nothing to undo!")
        return

    for src, dest in last_operations:
        file = os.path.join(dest, os.path.basename(src))
        if os.path.exists(file):
            shutil.move(file, src)

    logging.info("UNDO completed")
    messagebox.showinfo("Sortify", "Last operation undone!")

def open_log():
    os.startfile(LOG_FILE)

# ---------------- GUI ---------------- #

show_splash()

root = Tk()
root.title("Sortify – Smart File Organizer")
root.geometry("540x650")
root.resizable(False, False)
root.configure(bg="#1e1e1e")

# ✅ SAFE ICON LOADING (NO CRASH)
try:
    icon = PhotoImage(file=os.path.join(BASE_DIR, "sortify.png"))
    root.iconphoto(True, icon)
except Exception:
    pass

style = Style()
style.theme_use("default")
style.configure(
    "Dark.Horizontal.TProgressbar",
    troughcolor="#2b2b2b",
    background="#4FC3F7",
    thickness=18
)

Label(root, text="Sortify",
      font=("Segoe UI", 22, "bold"),
      bg="#1e1e1e", fg="#4FC3F7").pack(pady=(20, 0))

Label(root, text="Smart File Organizer",
      font=("Segoe UI", 11),
      bg="#1e1e1e", fg="#bbbbbb").pack(pady=(0, 20))

buttons = [
    ("📂 Select Folder", choose_folder),
    ("👁 Preview (Dry Run)", lambda: organize_files(preview=True)),
    ("⚡ Organize Files", organize_files),
    ("↩ Undo Last Operation", undo_last),
    ("📄 Open Log File", open_log),
]

for text, cmd in buttons:
    Button(root, text=text, command=cmd, width=36,
           font=("Segoe UI", 10),
           bg="#2b2b2b", fg="white",
           relief="flat", cursor="hand2",
           activebackground="#3a3a3a").pack(pady=6)

progress = Progressbar(root, length=440,
                       mode="determinate",
                       style="Dark.Horizontal.TProgressbar")
progress.pack(pady=(20, 5))

percent_label = Label(root, text="0%",
                      font=("Segoe UI", 10, "bold"),
                      bg="#1e1e1e", fg="#4FC3F7")
percent_label.pack()

status_label = Label(root, text="No folder selected",
                     wraplength=480,
                     font=("Segoe UI", 9),
                     bg="#1e1e1e", fg="#aaaaaa")
status_label.pack(pady=(10, 20))

root.mainloop()
