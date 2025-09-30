import os
from PyPDF2 import PdfReader, PdfWriter
import shutil

def append_pdfs(output, *inputs):
    """
    Append/concatenate multiple PDF files.

    Usage:
        append_pdfs(output, input1, input2, ...)
        append_pdfs(output, *input_list)

    Parameters
    ----------
    output : str
        Output PDF file path. If it exists, PDFs are appended.
    inputs : str or list of str
        Input PDF file(s) to append. Can be strings or a list of strings.

    Raises
    ------
    FileNotFoundError
        If any input file does not exist.
    """
    # Flatten input if a single list is passed
    if len(inputs) == 1 and isinstance(inputs[0], (list, tuple)):
        inputs = inputs[0]

    if len(inputs) < 1:
        raise ValueError("append_pdfs: Missing input filenames")

    # Ensure all input files exist, append .pdf if missing
    input_files = []
    for f in inputs:
        if not os.path.exists(f):
            if not f.lower().endswith(".pdf"):
                f_pdf = f + ".pdf"
                if os.path.exists(f_pdf):
                    f = f_pdf
                else:
                    raise FileNotFoundError(f"Input file {f} does not exist")
            else:
                raise FileNotFoundError(f"Input file {f} does not exist")
        input_files.append(f)

    # If output doesn't exist and only one input, copy directly
    if not os.path.exists(output) and len(input_files) == 1:
        shutil.copyfile(input_files[0], output)
        return

    # Create a temporary writer
    writer = PdfWriter()

    # If output exists, append its pages first
    if os.path.exists(output):
        reader_existing = PdfReader(output)
        for page in reader_existing.pages:
            writer.add_page(page)

    # Append all input PDFs
    for f in input_files:
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)

    # Write to output
    with open(output, "wb") as f_out:
        writer.write(f_out)
