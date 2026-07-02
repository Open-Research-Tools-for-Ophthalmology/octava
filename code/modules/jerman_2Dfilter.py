from .frangi_2Dfilter import hessian_filter, eig2im
import numpy as np

# Adapted from:
# https://github.com/timjerman/JermanEnhancementFilter/blob/master/vesselness2D.m
# https://github.com/mcgarrysd/vessel_metrics/blob/main/final_scripts/vessel_metrics.py
# https://github.com/scikit-image/scikit-image/pull/8074/changes#diff-c4d9acd2360fa044a07e7b15990290c46ede15951b42a712e301bb0a53a20097
# Only difference is we use self-contained hessian_filter functions
def jerman_2Dfilter(
    im,
    sigmas: np.ndarray = np.arange(1, 6, 1), # by default 1:5
    tau=0.75,
    brightondark=True,
):
    im = np.asarray(im, dtype=np.float64)
    vesselness = np.zeros_like(im, dtype=np.float64)

    for i, sigma in enumerate(sigmas):
        # 1. Hessian derivatives
        Dxx, Dxy, Dyy = hessian_filter(im, sigma)

        # 2. Normalize by sigma^2
        var = sigma ** 2
        Dxx *= var
        Dxy *= var
        Dyy *= var

        # reduce computation by computing vesselness only where needed
        # S.-F. Yang and C.-H. Cheng, “Fast computation of Hessian-based
        # enhancement filters for medical images,” Comput. Meth. Prog. Bio., vol.
        # 116, no. 3, pp. 215–225, 2014.
        # Trace = B1, Det(erminant) = B2 (line 84 / vesselness2D)
        trace = Dxx + Dyy
        det = Dxx * Dyy - Dxy ** 2
        degenerate = (trace == 0) & (det == 0)
        # Mask = indeces = find(T==1) = ~T
        if brightondark:
            mask = (trace <= 0) & ~degenerate
        else:
            mask = (trace >= 0) & ~degenerate

        # m_major, m_minor = Lambda1i,Lambda2i (line 114 / vesselness2D)
        # TODO check if we need to Dxx = Dxx(mask) to match vesselness2D? (line 105 / vesselness2D) or is this just for efficiency?
        _, _, m_major, m_minor = eig2im(Dxx, Dxy, Dyy)
        m_major = np.where(mask, m_major, 0)
        m_minor = np.where(mask, m_minor, 0)

        # some noise removal (line 120 / vesselness2D)
        m_major[np.abs(m_major) < 1e-4] = 0
        m_minor[np.abs(m_minor) < 1e-4] = 0

        # Negate at brightondark to make lambda positive values, Line 43 / vesselness2D
        Lambda2 = -m_major if brightondark else m_major

        # 2D adaptation: Lambda3 = Lambda2, only two eigenvalues exist in 2D; (line 47 / vesselness2D)
        Lambda3 = Lambda2.copy()

        # Lambda_rho regularisation (line 50 / vesselness2D).
        Lambda_rho = Lambda3.copy()
        Lambda3_max = float(np.max(Lambda3))
        low_indeces = (Lambda3 > 0) & (Lambda3 <= tau * Lambda3_max)
        Lambda_rho[low_indeces] = tau * Lambda3_max
        Lambda_rho[Lambda3 <= 0] = 0

        # Vesselness response (line 53 / vesselness2D).
        with np.errstate(invalid='ignore', divide='ignore'): # NaN case handled in normalisation step
            response = (Lambda2 ** 2 * (Lambda_rho - Lambda2) * 27 / ((Lambda2 + Lambda_rho) ** 3))

        # 0,1 Normlisation (line 55 / vesselness2D).
        response[(Lambda2 >= Lambda_rho / 2) & (Lambda_rho > 0)] = 1
        response[(Lambda2 <= 0) | (Lambda_rho <= 0)] = 0
        response[~np.isfinite(response)] = 0

        # max response over multiple scales (line 59 / vesselness2D).
        if sigma == 1:
            vesselness = response
        else:
            vesselness = np.maximum(vesselness, response)

    # should not be really needed as already normlised, but keep consistent as (line 69 / vesselness2D)... 
    vesselness = vesselness / float(np.max(vesselness))
    vesselness[vesselness < 1e-2] = 0

    return vesselness