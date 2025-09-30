import os
import subprocess
import sys
import platform
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog

def pdftops(cmd=None):
    if cmd is None:
        xpdf_path()  # Will raise error if not found
        return

    path = xpdf_path()
    command = xpdf_command(path) + cmd
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return (result.returncode, result.stdout + result.stderr)


def xpdf_path():
    path_ = user_string('pdftops')
    if check_xpdf_path(path_):
        return path_

    bin = 'pdftops.exe' if os.name == 'nt' else 'pdftops'

    if check_store_xpdf_path(bin):
        return bin

    common_paths = [
        r'C:\Program Files\xpdf\pdftops.exe',
        r'C:\Program Files (x86)\xpdf\pdftops.exe',
        '/usr/bin/pdftops',
        '/usr/local/bin/pdftops'
    ]
    for p in common_paths:
        if check_store_xpdf_path(p):
            return p

    # If we reach here, ask user via GUI
    return gui_locate_pdftops(bin)


def gui_locate_pdftops(bin):
    errMsg1 = ("Pdftops utility not found. Please locate the program, "
               "or install xpdf-tools from http://xpdfreader.com/download.html\n\n")
    errMsg2 = ('"Xpdf command line tools" section')

    root = tk.Tk()
    root.withdraw()  # hide main window

    # Show initial message box
    response = messagebox.askquestion(
        "Pdftops error",
        errMsg1 + "Install pdftops?\n\n"
        "Press 'No' to locate pdftops manually.",
        icon='warning'
    )

    while True:
        if response == 'yes':
            webbrowser.open('http://xpdfreader.com/download.html')
            # After user installs, ask if they want to locate manually now
            response = messagebox.askquestion(
                "Pdftops error",
                "Have you installed pdftops? Locate now?",
                icon='question'
            )
            if response == 'no':
                break

        if response == 'no':
            # Ask user to locate pdftops executable
            file_path = filedialog.askopenfilename(
                title="Locate pdftops executable",
                initialdir="/",
                filetypes=[("Executables", "*.exe" if os.name == 'nt' else "*")]
            )
            if not file_path:
                # User cancelled
                break

            # Try some common subdirs
            dirs_to_try = ['', 'bin', 'lib']
            for d in dirs_to_try:
                trial_path = os.path.join(os.path.dirname(file_path), d, bin)
                if os.path.isfile(trial_path) and check_store_xpdf_path(trial_path):
                    root.destroy()
                    return trial_path

            # Check the selected file itself
            if check_store_xpdf_path(file_path):
                root.destroy()
                return file_path

            messagebox.showerror("Error", f"Selected file is not a valid pdftops executable.\nPlease try again.")
            response = messagebox.askquestion("Pdftops error", "Try again?", icon='question')

        else:
            # Any other answer, break out
            break

    root.destroy()
    raise FileNotFoundError("pdftops executable not found.")


def check_store_xpdf_path(path_):
    if check_xpdf_path(path_):
        if not user_string('pdftops', path_):
            print(f"Warning: Could not save path to pdftops. Enter it manually.")
        return True
    return False


def check_xpdf_path(path_):
    try:
        command = xpdf_command(path_) + '-h'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return 'PostScript' in result.stdout
    except Exception as e:
        if os.path.isfile(path_) and ('/' in path_ or '.' in path_):
            print(f"Error running {path_}:\n{e}")
        return False


def xpdf_command(path_):
    shell_cmd = ''
    if sys.platform.startswith('linux'):
        shell_cmd = 'export LD_LIBRARY_PATH=""; '
    elif sys.platform == 'darwin':
        shell_cmd = 'export DYLD_LIBRARY_PATH=""; '

    return f'{shell_cmd}"{path_}" '


def user_string(key, value=None):
    settings_file = os.path.expanduser(f'~/.{key}.txt')

    if value is None:
        if os.path.isfile(settings_file):
            with open(settings_file, 'r') as f:
                return f.read().strip()
        return ''
    else:
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                f.write(value)
            return True
        except Exception:
            return False