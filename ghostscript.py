import os
import sys
import subprocess
import platform
import tkinter as tk
from tkinter import filedialog, messagebox

# Persistent storage for Ghostscript path (like MATLAB user_string)
GS_PATH_FILE = os.path.join(os.path.expanduser("~"), ".ghostscript_path.txt")

def ghostscript(cmd):
    """
    Calls a local Ghostscript executable with the input command.
    
    Parameters
    ----------
    cmd : str
        Command string to pass to Ghostscript.
    
    Returns
    -------
    status : int
        0 if command ran without problem, nonzero otherwise.
    result : str
        Output from Ghostscript.
    """
    path_ = gs_path()
    try:
        full_cmd = gs_command(path_) + cmd
        completed = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        status = completed.returncode
        result = completed.stdout + completed.stderr
        return status, result
    except Exception as err:
        url1 = 'https://github.com/altmany/export_fig/issues/12#issuecomment-61467998'
        url2 = 'https://github.com/altmany/export_fig/issues/20#issuecomment-63826270'
        url3 = 'https://github.com/altmany/export_fig/issues/27'
        msg = f"Ghostscript error. Try rolling back to GS 9.10: {url1}\n"
        msg += f"Possible font path issue on Unix/Mac: {url3}\n"
        messagebox.showerror("Ghostscript Error", msg)
        raise err

def gs_path():
    """Return a valid Ghostscript path, prompting the user if necessary."""
    path_ = load_gs_path()
    if check_gs_path(path_):
        return path_

    # Check common binary locations
    if sys.platform.startswith("win"):
        candidates = ["gswin32c.exe", "gswin64c.exe", "gs"]
        default_dirs = [r"C:\Program Files\gs", r"C:\Program Files (x86)\gs"]
        for d in default_dirs:
            if os.path.exists(d):
                for sub in os.listdir(d):
                    for exe in candidates:
                        candidate = os.path.join(d, sub, "bin", exe)
                        if os.path.isfile(candidate) and check_store_gs_path(candidate):
                            return candidate
    else:
        candidates = ["/usr/bin/gs", "/usr/local/bin/gs"]
        for candidate in candidates:
            if os.path.isfile(candidate) and check_store_gs_path(candidate):
                return candidate

    # Ask user via dialog
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Locate Ghostscript", "Ghostscript installation not found. Please locate the program.")
    base = filedialog.askdirectory(title="Locate Ghostscript installation")
    if base:
        for subdir in ["", "bin", "lib"]:
            for exe in ["gswin32c.exe", "gswin64c.exe", "gs"] if sys.platform.startswith("win") else ["gs"]:
                path_ = os.path.join(base, subdir, exe)
                if os.path.isfile(path_) and check_store_gs_path(path_):
                    return path_

    url = "http://pages.uoregon.edu/koch" if sys.platform == "darwin" else "http://ghostscript.com"
    raise FileNotFoundError(f"Ghostscript not found. Install from {url}.")

def check_store_gs_path(path_):
    """Check if path is valid and store it for future use."""
    if check_gs_path(path_):
        save_gs_path(path_)
        return True
    return False

def check_gs_path(path_):
    """Check if Ghostscript executable works."""
    if not path_:
        return False
    try:
        completed = subprocess.run([path_, "-h"], capture_output=True, text=True)
        return completed.returncode == 0
    except Exception:
        return False

def gs_command(path_):
    """Return the system call for Ghostscript with environment prep for Unix/Mac."""
    shell_cmd = ""
    if sys.platform.startswith("linux"):
        shell_cmd = 'export LD_LIBRARY_PATH=""; '
    elif sys.platform == "darwin":
        shell_cmd = 'export DYLD_LIBRARY_PATH=""; '
    return f'{shell_cmd}"{path_}" '

def load_gs_path():
    """Load Ghostscript path from persistent file."""
    if os.path.isfile(GS_PATH_FILE):
        with open(GS_PATH_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_gs_path(path_):
    """Save Ghostscript path for future use."""
    try:
        with open(GS_PATH_FILE, "w", encoding="utf-8") as f:
            f.write(path_)
        return True
    except Exception:
        return False
