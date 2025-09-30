def fix_lines(fstrm, fname2=None):
    import re

    # If fname2 is provided, treat fstrm as a filename
    if fname2 is not None or isinstance(fstrm, str):
        if fname2 is None:
            fname2 = fstrm
        fstrm = read_write_entire_textfile(fstrm)  # read file

    # Move embedded fonts after postscript header
    if fstrm.startswith('%!PS-AdobeFont-'):
        ind = [m.start() for m in re.finditer(r'[\n\r]%!PS-Adobe-', fstrm)]
        ind2 = [m.start() for m in re.finditer(r'[\n\r]%%EndComments[\n\r]+', fstrm)]
        if ind and ind2 and ind[0] < ind2[0]:
            fstrm = fstrm[ind[0]+1:ind2[0]] + fstrm[:ind[0]] + fstrm[ind2[0]+1:]

    # Adjust line styles
    ind = sorted([m.start() for m in re.finditer(r'[\n\r](SO|DO|DA|DD)[\n\r]', fstrm)])
    ind2 = [m.start() for m in re.finditer(r'[\n\r]\d* w[\n\r]', fstrm)]
    b = 0
    m = len(ind)
    n = len(ind2)
    for a in range(m):
        while b < n and ind2[b] < ind[a]:
            b += 1
        if b >= n:
            break
        if a < m-1 and ind2[b] > ind[a+1]:
            continue
        if (ind2[b] - ind[a]) > 8:
            continue
        # Swap line style command below line width command
        fstrm = fstrm[:ind[a]+1] + fstrm[ind[a]+4:ind2[b]+3] + fstrm[ind[a]+1:ind[a]+4] + fstrm[ind2[b]+3:]
        b += 1

    # Adjust grid lines (DO -> GR)
    ind = [m.start() for m in re.finditer(r'[\n\r]DO[\n\r]', fstrm)]
    if ind:
        ind2 = [m.start() for m in re.finditer(r'[\n\r] *\d* *\d* *mt *\d* *\d* *L[\n\r]', fstrm)]
        if ind2:
            for i, do_pos in enumerate(ind):
                for g_pos in ind2:
                    if 0 < g_pos - do_pos < 12:
                        # Replace DO with GR
                        fstrm = fstrm[:do_pos+1] + 'GR' + fstrm[do_pos+3:]
                        break

    # Define new styles
    new_style = [
        '/dom { dpi2point 1 currentlinewidth 0.08 mul add mul mul } bdef',
        '/dam { dpi2point 2 currentlinewidth 0.04 mul add mul mul } bdef',
        '/SO { [] 0 setdash 0 setlinecap } bdef',
        '/DO { [1 dom 1.2 dom] 0 setdash 0 setlinecap } bdef',
        '/DA { [4 dam 1.5 dam] 0 setdash 0 setlinecap } bdef',
        '/DD { [1 dom 1.2 dom 4 dam 1.2 dom] 0 setdash 0 setlinecap } bdef',
        '/GR { [0 dpi2point mul 4 dpi2point mul] 0 setdash 1 setlinecap } bdef'
    ]
    fstrm = re.sub(r'(% line types:.+?)/.+?%', lambda m: m.group(1) + '\r'.join(new_style) + '\r%', fstrm, flags=re.DOTALL)

    # Write file if fname2 is provided
    if fname2 is not None:
        read_write_entire_textfile(fname2, fstrm)

    return fstrm
