import numpy as np
from scipy.ndimage import convolve

def hessian_filter(I:np.ndarray, sigma:float=1)-> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the second-order derivatives (Hessian) of an image.

    Parameters:
        I (ndarray): Grayscale image (float32 or float64).
        sigma (float): Standard deviation of the Gaussian.

    Returns:
        Dxx, Dxy, Dyy (ndarrays): Second derivative components.
    """
    # Generate filter grid
    size = int(np.round(3 * sigma))
    x, y = np.meshgrid(np.arange(-size, size + 1),
                       np.arange(-size, size + 1))

    # Gaussian 2nd derivative filters
    normalization = 1 / (2 * np.pi * sigma**4)
    DGaussxx = normalization * ((x**2 / sigma**2) - 1) * np.exp(-(x**2 + y**2) / (2 * sigma**2))
    DGaussxy = (1 / (2 * np.pi * sigma**6)) * (x * y) * np.exp(-(x**2 + y**2) / (2 * sigma**2))
    DGaussyy = DGaussxx.T  # Transpose for symmetry

    # Convolve image with filters
    Dxx = convolve(I, DGaussxx, mode='reflect')
    Dxy = convolve(I, DGaussxy, mode='reflect')
    Dyy = convolve(I, DGaussyy, mode='reflect')

    return Dxx, Dxy, Dyy


def main():
    # Testing
    from skimage import io, img_as_float
    import matplotlib.pyplot as plt

    # Load grayscale image
    image = img_as_float(io.imread('/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif', as_gray=True))

    # Check shape and range
    print(image.shape, image.min(), image.max())

    Dxx, Dxy, Dyy = hessian_filter(image, sigma=2)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(Dxx, cmap='gray')
    axes[0].set_title('Dxx (∂²I/∂x²)')

    axes[1].imshow(Dxy, cmap='gray')
    axes[1].set_title('Dxy (∂²I/∂x∂y)')

    axes[2].imshow(Dyy, cmap='gray')
    axes[2].set_title('Dyy (∂²I/∂y²)')

    for ax in axes:
        ax.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()