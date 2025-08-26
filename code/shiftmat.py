import numpy as np

def shiftmat(A, n=0, dim=0, pad=0):
    A = np.asarray(A)

    # Scalar checks (match MATLAB's "must be scalar" spirit)
    if not np.isscalar(n) or not np.isscalar(dim) or not np.isscalar(pad):
        raise TypeError("n, dim, and pad must be scalars.")

    # MATLAB: round then cast to int
    n = int(round(float(n)))
    dim = int(dim)

    nd = A.ndim
    if n == 0 or dim < 0 or dim >= nd:
        return A.copy()

    L = A.shape[dim]
    k = min(abs(n), L)  # how many positions actually move

    # Promote dtype so `pad` never gets truncated (e.g., int array + float pad)
    out_dtype = np.result_type(A.dtype, np.asarray(pad).dtype)
    out = np.full(A.shape, pad, dtype=out_dtype)

    src = [slice(None)] * nd
    dst = [slice(None)] * nd

    if n > 0:
        # move data "down" the axis; pad goes at the start
        src[dim] = slice(0, L - k)
        dst[dim] = slice(k, L)
    else:
        # n < 0: move data "up" the axis; pad goes at the end
        src[dim] = slice(k, L)
        dst[dim] = slice(0, L - k)

    out[tuple(dst)] = A[tuple(src)]
    return out
