import numpy as np

def shiftmat(A: np.ndarray, n: int = 0, dim: int = 0, pad: int | float = 0) -> np.ndarray:
    """
    Shift the entries of an array along a specified dimension, padding with a constant value.

    Parameters:
        A (np.ndarray): Input array to shift.
        n (int): Number of positions to shift. Positive shifts towards higher indices, negative towards lower.
        dim (int): Axis along which to shift. Defaults to 0 (first axis).
        pad (int | float): Scalar value used to fill the vacated positions. Defaults to 0.

    Returns:
        np.ndarray: A new array of the same shape as A with entries shifted and padded.
    """
    # Argument Validation & Defaults
    A = np.asarray(A)

    if not isinstance(n, (int, np.integer)):
        raise TypeError("n must be an integer scalar")
    if not isinstance(dim, (int, np.integer)):
        raise TypeError("dim must be an integer")
    if not np.isscalar(pad):
        raise TypeError("pad must be a scalar")

    n = int(round(n))
    nd = A.ndim
    if dim < 0:
        dim = nd + 1
    #  Permutation Vector and Early Return
    if dim >= nd or n == 0:
        return A.copy()
    # Permute and Reshape to 2D
    dims = list(range(dim, max(nd, dim))) + list(range(0, dim))
    A_perm = np.transpose(A, axes=dims)
    orig_shape = A_perm.shape
    A_2d = A_perm.reshape((orig_shape[0], -1))
    # Determine Rows to Keep
    size = A_2d.shape[0]
    if n < 0:
        rows = np.arange(-n, size)
        B_2d = A_2d[rows, :]
    elif n > 0:
        rows = np.arange(0, size - n)
        B_2d = A_2d[rows, :]
    # Pad with pad Value
    pad_rows = min(abs(n), size)
    pad_shape = (pad_rows, A_2d.shape[1])
    pad_block = np.full(pad_shape, pad, dtype=A.dtype)

    if n < 0:
        B_2d = np.vstack([B_2d, pad_block])
    elif n > 0:
        B_2d = np.vstack([pad_block, B_2d])
    # Restore Shape and Axis Order
    restored_shape = (B_2d.shape[0],) + orig_shape[1:]
    B_restored = B_2d.reshape(restored_shape)
    inv_dims = np.argsort(dims)
    return np.transpose(B_restored, axes=inv_dims)
