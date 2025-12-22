from shiftmat import shiftmat
import numpy as np

A = np.arange(1, 7).reshape(3, 2)
print(A)
# [[1 2]
#  [3 4]
#  [5 6]]

print(shiftmat(A, 1, dim=0, pad=0))
# Expected:
# [[0 0]
#  [1 2]
#  [3 4]]

print(shiftmat(A, -1, dim=0, pad=0))
# Expected:
# [[3 4]
#  [5 6]
#  [0 0]]

B = np.arange(1, 10).reshape(3, 3)
print(B)
# [[1 2 3]
#  [4 5 6]
#  [7 8 9]]

print(shiftmat(B, 1, dim=1, pad=-1))
# Shift along columns, fill with -1
