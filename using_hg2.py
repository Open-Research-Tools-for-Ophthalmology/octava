# USING_HG2 Determine if the HG2 graphics engine is used
#
#   tf = using_hg2(fig=None)
#
# IN:
#   fig - handle to the figure in question (optional).
#
# OUT:
#   tf - always True, since Python/Matplotlib does not have
#        the HG1 vs HG2 distinction. Matplotlib is inherently
#        object-oriented and closer to MATLAB's HG2.
#
# Notes:
# - This function is kept for compatibility with MATLAB code,
#   but the check is unnecessary in Python.

def using_hg2(fig=None):
    return True
