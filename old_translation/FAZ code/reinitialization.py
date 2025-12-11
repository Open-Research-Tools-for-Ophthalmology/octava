import numpy as np
from copy import deepcopy

def reinitialization(phi: np.ndarray, dt: float) -> np.ndarray:
    """
    Reinitializes a level set function phi to be a signed distance function.

    Parameters:
    - phi: 2D numpy array representing the level set function.
    - dt: time step for iteration.

    Returns:
    - Updated 2D numpy array phi after reinitialization.
    """
    eps = 1e-8  # Small value to avoid division by zero

    for _ in range(10):  # Run up to 10 iterations
        old = deepcopy(phi)  # Save current phi for convergence check

        # Compute backward difference in rows (a): φ_i,j - φ_{i-1,j}
        a = phi - np.vstack((phi[0:1, :], phi[:-1, :]))
        # Compute forward difference in rows (b): φ_{i+1,j} - φ_i,j
        b = np.vstack((phi[1:, :], phi[-1:, :])) - phi
        # Compute backward difference in cols (c): φ_i,j - φ_{i,j-1}
        c = phi - np.hstack((phi[:, 0:1], phi[:, :-1]))
        # Compute forward difference in cols (d): φ_{i,j+1} - φ_i,j
        d = np.hstack((phi[:, 1:], phi[:, -1:])) - phi

        G = np.zeros_like(phi)  # Initialize gradient magnitude correction array

        pos_mask = phi > 0  # Boolean mask for φ > 0
        neg_mask = phi < 0  # Boolean mask for φ < 0

        # For φ > 0, use Godunov's scheme:
        # sqrt(max(a⁺², b⁻²) + max(c⁺², d⁻²)) - 1
        G[pos_mask] = np.sqrt(
            np.maximum(np.maximum(a[pos_mask], 0)**2, np.minimum(b[pos_mask], 0)**2) +
            np.maximum(np.maximum(c[pos_mask], 0)**2, np.minimum(d[pos_mask], 0)**2)
        ) - 1

        # For φ < 0, similar but with flipped sign directions:
        # sqrt(max(a⁻², b⁺²) + max(c⁻², d⁺²)) - 1
        G[neg_mask] = np.sqrt(
            np.maximum(np.minimum(a[neg_mask], 0)**2, np.maximum(b[neg_mask], 0)**2) +
            np.maximum(np.minimum(c[neg_mask], 0)**2, np.maximum(d[neg_mask], 0)**2)
        ) - 1

        # Compute smoothed sign function: sign(phi)
        # Avoids division by zero using eps
        S = phi / (np.abs(phi) + eps)

        # Update φ using reinitialization PDE: φₙ₊₁ = φₙ - dt * sign(φ₀) * (|∇φ| - 1)
        phi = phi - dt * S * G

        # Identify points near the zero level set (narrow band |φ| ≤ 1)
        narrow_band = np.abs(phi) <= 1 # turned into a mask
        M = np.sum(narrow_band)  # Number of points in narrow band

        if M > 0:
            # Compute average change in φ over the narrow band
            Q = np.sum(np.abs(phi[narrow_band] - old[narrow_band])) / M
            # If average change is small enough, consider converged and stop early
            if Q <= dt * 1**2:
                break

    return phi

