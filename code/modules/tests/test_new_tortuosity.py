import scipy.io as sio
import numpy as np
import json
from types import SimpleNamespace
import csv
from modules.skeletonise import skeletonise
from modules.biomarker import BiomarkerAnalyzer


class DummyVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


class DummyCanvas(SimpleNamespace):
    def __init__(self):
        super().__init__()
        self._image_refs = {}

    # GUI-dependent methods used by skeletonise(display=False won't call most)
    def create_image(self, *args, **kwargs):
        return None


# Load binary image
data = sio.loadmat(
    "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/old_translation/Skeletonization/matlab_skels/binarise_python_result.mat"
)
python_bin_img = data["Y_py"]

# Ensure binary is boolean/uint8 as needed
bin_img = (python_bin_img > 0).astype(np.uint8)
raw_img = (bin_img * 255).astype(np.uint8)

# Build dummy canvas
canvas = DummyCanvas()
canvas.binary_image = bin_img
canvas.twig_size = DummyVar(10)
canvas.image_size_var = DummyVar(3.0)          # mm
canvas.fullImSizePix = bin_img.shape           # (height, width)
canvas.current_save_folder = "/tmp"
canvas.FileLabelName = "test_image"

# Run skeletonisation
skel2, nodes, links = skeletonise(canvas, raw_img, bin_img, display=False)

# Run tortuosity metrics
BiomarkerAnalyzer.new_torturosity_metrics(canvas)

# Save results
out_npz = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/modules/tests/python_tortuosity_metrics.npz"
out_json = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/modules/tests/python_tortuosity_metrics.json"

np.savez(
    out_npz,
    skeleton=canvas.skeleton_image,
    per_link_metrics=canvas.tortuosity_metrics_per_link,
    mean_metrics=canvas.tortuosity_mean_metrics,
)

with open(out_json, "w") as f:
    json.dump(canvas.tortuosity_mean_metrics, f, indent=2)

out_csv = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/modules/tests/python_tortuosity_metrics.csv"

with open(out_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value"])
    for k, v in canvas.tortuosity_mean_metrics.items():
        writer.writerow([k, v])

print("Python tortuosity metrics saved.")
print(canvas.tortuosity_mean_metrics)