import os
import subprocess
import tempfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


def run_ghostscript(options):
    try:
        result = subprocess.run(['gs'] + options, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        messagebox.showerror("Error", "Ghostscript executable 'gs' not found. Please install it and add to PATH.")
        return 1, "Ghostscript not found"


def font_path():
    # Mimic MATLAB font_path logic
    fp = os.environ.get('GS_FONTPATH')
    if fp:
        return fp
    if os.name == 'nt':  # Windows
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        return f"{fp + ';' if fp else ''}{windir}\\Fonts"
    else:
        # Linux/Unix default font paths
        paths = [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            '/usr/share/fonts/X11',
            '/usr/local/share/fonts/X11',
            '/usr/share/fonts/truetype',
            '/usr/local/share/fonts/truetype',
        ]
        return (fp + ':' if fp else '') + ':'.join(paths)


def eps2pdf(source, dest, crop=True, append=False, gray=False, quality=None, gs_options=None):
    """
    Convert an EPS file to PDF using Ghostscript with options.

    Args:
        source (str): EPS source filename.
        dest (str): PDF destination filename.
        crop (bool): Crop output PDF.
        append (bool): Append EPS as new page if dest exists.
        gray (bool): Output grayscale PDF.
        quality (int or None): Image quality, >100 means lossless.
        gs_options (list or None): Additional ghostscript options.
    """
    downsample_opts = [
        '-dDownsampleColorImages=false',
        '-dDownsampleGrayImages=false',
        '-dDownsampleMonoImages=false',
    ]

    options = [
        '-q', '-dNOPAUSE', '-dBATCH',
        '-sDEVICE=pdfwrite',
        '-dPDFSETTINGS=/prepress',
        *downsample_opts,
        f'-sOutputFile={dest}'
    ]

    if crop:
        options.append('-dEPSCrop')

    fp = font_path()
    if fp:
        options.append(f'-sFONTPATH={fp}')

    if gray:
        options.extend([
            '-sColorConversionStrategy=Gray',
            '-dProcessColorModel=/DeviceGray'
        ])

    if quality is not None:
        if quality > 100:
            options.extend([
                '-dAutoFilterColorImages=false',
                '-dAutoFilterGrayImages=false',
                '-dColorImageFilter=/FlateEncode',
                '-dGrayImageFilter=/FlateEncode',
                '-c',
                '.setpdfwrite << /ColorImageDownsampleThreshold 10 /GrayImageDownsampleThreshold 10 >> setdistillerparams'
            ])
        else:
            options.extend([
                '-dAutoFilterColorImages=false',
                '-dAutoFilterGrayImages=false',
                '-dColorImageFilter=/DCTEncode',
                '-dGrayImageFilter=/DCTEncode',
            ])
            v = 1 + (quality < 80)
            quality_factor = 1 - quality / 100
            s = f"<< /QFactor {quality_factor:.2f} /Blend 1 /HSample [{v} 1 1 {v}] /VSample [{v} 1 1 {v}] >>"
            options.extend([
                '-c',
                f'.setpdfwrite << /ColorImageDict {s} /GrayImageDict {s} >> setdistillerparams'
            ])

    if gs_options:
        if isinstance(gs_options, list):
            options.extend(gs_options)
        elif isinstance(gs_options, str):
            options.append(gs_options)
        else:
            raise ValueError("gs_options must be a string or list of strings")

    if append and os.path.isfile(dest):
        orig_size = os.path.getsize(dest)
        tempdir = tempfile.gettempdir()

        tmp_nam = os.path.join(tempdir, next(tempfile._get_candidate_names()) + '.pdf')
        try:
            shutil.copy(dest, tmp_nam)
        except PermissionError:
            tmp_nam = dest + '.bak.pdf'
            shutil.copy(dest, tmp_nam)

        # Convert EPS to interim PDF
        status, msg = run_ghostscript(options + ['-f', source])
        if status != 0:
            messagebox.showerror("Ghostscript error", f"Failed to convert EPS to PDF:\n{msg}")
            return

        tmp_nam2 = os.path.join(tempdir, next(tempfile._get_candidate_names()) + '.pdf')
        shutil.copy(dest, tmp_nam2)

        # Append PDFs: original (tmp_nam) and interim (tmp_nam2)
        options_append = options.copy()
        options_append += ['-f', tmp_nam, tmp_nam2]

        status, msg = run_ghostscript(options_append)
        if status != 0 or os.path.getsize(dest) < orig_size + 100:
            # Try appending EPS directly
            options_direct = options.copy()
            options_direct += ['-f', tmp_nam, source]
            status, msg = run_ghostscript(options_direct)
            if status != 0:
                messagebox.showerror("Ghostscript error", f"Failed to append EPS:\n{msg}")
                return

        os.remove(tmp_nam)
        os.remove(tmp_nam2)

    else:
        # Just convert EPS to PDF
        options.append('-f')
        options.append(source)
        status, msg = run_ghostscript(options)
        if status != 0:
            messagebox.showerror("Ghostscript error", f"Failed to convert EPS to PDF:\n{msg}")
            return

    messagebox.showinfo("Success", f"Converted '{source}' to '{dest}' successfully.")


# --- Simple Tkinter GUI ---

class EPS2PDFApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPS to PDF Converter")
        self.geometry("450x300")

        # Source EPS
        tk.Label(self, text="Source EPS file:").pack(anchor='w')
        self.source_entry = tk.Entry(self, width=60)
        self.source_entry.pack()
        tk.Button(self, text="Browse EPS", command=self.browse_eps).pack()

        # Destination PDF
        tk.Label(self, text="Destination PDF file:").pack(anchor='w')
        self.dest_entry = tk.Entry(self, width=60)
        self.dest_entry.pack()
        tk.Button(self, text="Browse PDF", command=self.browse_pdf).pack()

        # Options
        self.crop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="Crop PDF", variable=self.crop_var).pack(anchor='w')

        self.append_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Append if PDF exists", variable=self.append_var).pack(anchor='w')

        self.gray_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Grayscale output", variable=self.gray_var).pack(anchor='w')

        self.quality_var = tk.StringVar(value="")
        tk.Label(self, text="Image quality (1-100, >100 lossless):").pack(anchor='w')
        self.quality_entry = tk.Entry(self, textvariable=self.quality_var, width=10)
        self.quality_entry.pack(anchor='w')

        self.gs_options_var = tk.StringVar()
        tk.Label(self, text="Additional Ghostscript options (space-separated):").pack(anchor='w')
        self.gs_options_entry = tk.Entry(self, textvariable=self.gs_options_var, width=60)
        self.gs_options_entry.pack()

        tk.Button(self, text="Convert EPS to PDF", command=self.convert).pack(pady=10)

    def browse_eps(self):
        filename = filedialog.askopenfilename(filetypes=[("EPS files", "*.eps"), ("All files", "*.*")])
        if filename:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, filename)

    def browse_pdf(self):
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if filename:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, filename)

    def convert(self):
        source = self.source_entry.get()
        dest = self.dest_entry.get()
        crop = self.crop_var.get()
        append = self.append_var.get()
        gray = self.gray_var.get()
        quality_str = self.quality_var.get().strip()
        gs_opts_str = self.gs_options_var.get().strip()

        if not os.path.isfile(source):
            messagebox.showerror("Error", "Source EPS file does not exist.")
            return
        if not dest:
            messagebox.showerror("Error", "Please specify destination PDF file.")
            return

        quality = None
        if quality_str:
            try:
                quality = int(quality_str)
            except ValueError:
                messagebox.showerror("Error", "Quality must be an integer.")
                return

        gs_opts = gs_opts_str.split() if gs_opts_str else None

        try:
            eps2pdf(source, dest, crop=crop, append=append, gray=gray, quality=quality, gs_options=gs_opts)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert:\n{e}")


if __name__ == "__main__":
    app = EPS2PDFApp()
    app.mainloop()
