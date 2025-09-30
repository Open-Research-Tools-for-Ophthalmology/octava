def read_write_entire_textfile(fname, fstrm=None):
    """
    Read or write an entire text file, MATLAB-style.
    
    Reading:
        fstrm = read_write_entire_textfile(fname)
    
    Writing:
        read_write_entire_textfile(fname, fstrm)
    
    EPS files are read/written in latin1 encoding for compatibility.
    """
    if fstrm is None:
        # Reading
        try:
            with open(fname, 'r', encoding='latin1') as fh:
                return fh.read()
        except OSError as e:
            raise RuntimeError(f"Unable to open file {fname}.") from e
    else:
        # Writing
        if not isinstance(fstrm, str):
            raise TypeError("fstrm must be a string when writing text files.")
        try:
            with open(fname, 'w', encoding='latin1') as fh:
                fh.write(fstrm)
        except OSError as e:
            raise RuntimeError(f"Unable to write file {fname}.") from e
        return fstrm
