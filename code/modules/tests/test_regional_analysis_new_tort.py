import os
import sys

import numpy as np


current_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from modules.regional_analysis import normalize_regional_tortuosity_metrics


def test_normalize_regional_tortuosity_metrics_converts_nan_to_zero():
    metrics = {
        "PWAOC_mean": np.nan,
        "PWAOC_std": np.nan,
        "SOAM_mean": np.nan,
        "SOAM_std": np.nan,
    }

    assert normalize_regional_tortuosity_metrics(metrics) == {
        "PWAOC_mean": 0.0,
        "PWAOC_std": 0.0,
        "SOAM_mean": 0.0,
        "SOAM_std": 0.0,
    }


def test_normalize_regional_tortuosity_metrics_keeps_finite_values():
    metrics = {
        "PWAOC_mean": 1.25,
        "PWAOC_std": 0.1,
        "SOAM_mean": 2.5,
        "SOAM_std": 0.3,
    }

    assert normalize_regional_tortuosity_metrics(metrics) == metrics
