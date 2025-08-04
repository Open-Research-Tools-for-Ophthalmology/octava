import numpy as np

def reinitialization(phi: np.ndarray, dt: float) -> np.ndarray:
    """
    Reinitializes the level set function `phi` using the signed distance formulation.

    This function iteratively updates `phi` to maintain its property as a signed distance function, using a narrow band around the zero level set. It applies upwind schemes to compute derivatives and checks for convergence using average change within |phi| <= 1.

    Parameters:
        phi (np.ndarray): 2D array representing the level set function.
        dt (float): Time step for the update iterations.

    Returns:
        np.ndarray: The reinitialized level set function.
    """
    phi = phi.astype(np.float64)

    for _ in range(10):
        old = phi.copy()

        # Finite differences
        a = phi - np.vstack((phi[0:1, :], phi[:-1, :]))        # backward y
        b = np.vstack((phi[1:, :], phi[-1:, :])) - phi         # forward y
        c = phi - np.hstack((phi[:, 0:1], phi[:, :-1]))        # backward x
        d = np.hstack((phi[:, 1:], phi[:, -1:])) - phi         # forward x

        G = np.zeros_like(phi)

        pos = phi > 0
        neg = phi < 0

        # Positive values
        G[pos] = (
            np.sqrt(
                np.maximum(np.maximum(a[pos], 0) ** 2, np.minimum(b[pos], 0) ** 2) +
                np.maximum(np.maximum(c[pos], 0) ** 2, np.minimum(d[pos], 0) ** 2)
            ) - 1
        )

        # Negative values
        G[neg] = (
            np.sqrt(
                np.maximum(np.minimum(a[neg], 0) ** 2, np.maximum(b[neg], 0) ** 2) +
                np.maximum(np.minimum(c[neg], 0) ** 2, np.maximum(d[neg], 0) ** 2)
            ) - 1
        )

        S = phi / (np.abs(phi) + np.finfo(float).eps)
        phi = phi - dt * S * G

        # Convergence check
        ind = np.abs(phi) <= 1
        M = np.count_nonzero(ind)
        if M > 0:
            Q = np.sum(np.abs(phi[ind] - old[ind])) / M
            if Q <= dt:
                return phi

    return phi


#Testing
import numpy as np
import scipy.io

# Load phi and dt from .mat file
data = scipy.io.loadmat('phi_input.mat')
phi = data['phi']
dt = float(data['dt'])

phi_reinit_py = reinitialization(phi, dt)
scipy.io.savemat('phi_reinit_py.mat', {'phi_reinit_py': phi_reinit_py})

phi_matlab = data['phi_reinit']  # from MATLAB
error = np.abs(phi_matlab - phi_reinit_py)
print("Max difference:", np.max(error))
print("Mean difference:", np.mean(error))

# Optionally check correlation
corr = np.corrcoef(phi_matlab.flatten(), phi_reinit_py.flatten())[0, 1]
print("Correlation:", corr) # result: 1