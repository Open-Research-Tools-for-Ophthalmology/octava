import numpy as np

###############################################################################
# MATLAB-COMPATIBLE BWLOOKUP (EXACT BIT ORDERING)
###############################################################################

def bwlookup(A, lut):
    """
    Exact MATLAB version of bwlookup(A, lut)
    Supports ONLY 3×3 LUT here (512 elements), used for skeleton.
    """
    A = (A != 0)

    # Safety check — must be (512,)
    assert lut.ndim == 1, f"LUT must be 1-D, got shape {lut.shape}"
    assert lut.size == 512, f"LUT size must be 512, got {lut.size}"

    # pad with 0s exactly like MATLAB
    B = np.pad(A, 1, mode='constant')

    h, w = A.shape

    # Extract MATLAB bit positions (1,4,7; 2,5,8; 3,6,9)
    p1 = B[0:h,     0:w    ]  # bit0
    p2 = B[1:h+1,   0:w    ]  # bit1
    p3 = B[2:h+2,   0:w    ]  # bit2

    p4 = B[0:h,     1:w+1  ]  # bit3
    p5 = B[1:h+1,   1:w+1  ]  # bit4 (center)
    p6 = B[2:h+2,   1:w+1  ]  # bit5

    p7 = B[0:h,     2:w+2  ]  # bit6
    p8 = B[1:h+1,   2:w+2  ]  # bit7
    p9 = B[2:h+2,   2:w+2  ]  # bit8

    idx = (
        (p1 << 0) |
        (p2 << 1) |
        (p3 << 2) |
        (p4 << 3) |
        (p5 << 4) |
        (p6 << 5) |
        (p7 << 6) |
        (p8 << 7) |
        (p9 << 8)
    ).astype(np.uint16)

    return lut[idx]


###############################################################################
# LUTSKEL(i) — EXACT MATLAB TABLES
###############################################################################

def lutskel(i):
    lut_tables = {
        1: LUT1,
        2: LUT2,
        3: LUT3,
        4: LUT4,
        5: LUT5,
        6: LUT6,
        7: LUT7,
        8: LUT8
    }

    lut = lut_tables[i]

    # Enforce correct shape
    lut = np.asarray(lut, dtype=bool).reshape(-1)

    # Validate at call time
    assert lut.size == 512, f"LUT{i} must have 512 entries, got {lut.size}"

    return lut


###############################################################################
# SKELETON OPERATION (single iteration)
###############################################################################

def skel_apply_once(bw):
    out = bw.copy()
    for i in range(1, 9):
        lut = lutskel(i)
        out = bwlookup(out, lut)
    return out


###############################################################################
# ALG BWMORPH — MATLAB SKELETON LOGIC ONLY
###############################################################################

def algbwmorph_skeleton(bw, n):
    if n < 1:
        return bw, None

    infinite = np.isinf(n)
    current = bw.copy()
    iterations = 0

    while True:
        last = current.copy()
        current = skel_apply_once(current)
        iterations += 1

        if np.array_equal(last, current):
            break
        if not infinite and iterations >= n:
            break

    return current, None


###############################################################################
# BWMORPH WRAPPER (only case 'skeleton')
###############################################################################

def bwmorph_skeleton(bw, n=np.inf):
    bw = (bw != 0).astype(bool)
    out, _ = algbwmorph_skeleton(bw, n)
    return out


###############################################################################
# INSERT YOUR LUT ARRAYS HERE (lut1–lut8)
# MUST BE EXACTLY 512 BOOLS EACH
###############################################################################

LUT1 = np.array([...], dtype=bool).reshape(512)
LUT2 = np.array([...], dtype=bool).reshape(512)
LUT3 = np.array([...], dtype=bool).reshape(512)
LUT4 = np.array([...], dtype=bool).reshape(512)
LUT5 = np.array([...], dtype=bool).reshape(512)
LUT6 = np.array([...], dtype=bool).reshape(512)
LUT7 = np.array([...], dtype=bool).reshape(512)
LUT8 = np.array([...], dtype=bool).reshape(512)