import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

def pdf2eps(source, dest):
    # Construct the options list for pdftops
    options = ['pdftops', '-q', '-paper', 'match', '-eps', '-level2', source, dest]

    try:
        # Run pdftops command
        result = subprocess.run(options, capture_output=True, text=True)

        if result.returncode != 0:
            # If error message exists, show it, else show generic error
            msg = result.stderr.strip() or "Unable to generate EPS. Check destination directory is writable."
            raise RuntimeError(msg)

        # Fix the DSC error created by pdftops
        with open(dest, 'r+b') as f:
            lines = f.readlines()
            if len(lines) > 1 and lines[1].startswith(b'% Produced by'):
                # Replace leading space with '%'
                lines[1] = b'%' + lines[1][1:]
                f.seek(0)
                f.writelines(lines)

    except Exception as e:
        messagebox.showerror("Error", str(e))
        return False

    messagebox.showinfo("Success", f"Converted:\n{source}\nto\n{dest}")
    return True

def select_files_and_convert():
    source = filedialog.askopenfilename(
        title="Select PDF file",
        filetypes=[("PDF files", "*.pdf")]
    )
    if not source:
        return

    dest = filedialog.asksaveasfilename(
        title="Save EPS file as",
        defaultextension=".eps",
        filetypes=[("EPS files", "*.eps")]
    )
    if not dest:
        return

    pdf2eps(source, dest)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("PDF to EPS Converter")
    root.geometry("300x100")
    root.resizable(False, False)

    btn = tk.Button(root, text="Select PDF and Convert to EPS", command=select_files_and_convert)
    btn.pack(expand=True, pady=20)

    root.mainloop()