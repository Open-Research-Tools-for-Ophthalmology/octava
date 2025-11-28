# test_biomarkers_strict.py
import os, tempfile
import numpy as np
import pandas as pd
from generateBiomarkers import compute_biomarkers  # change module name if needed


class Box:  # tiny stub object
    pass


def make_label():
    l = Box(); l.Text = ""; return l  # mimic UI label with .Text


def build_app(tmpdir):
    app = Box()
    app.batchSaveFile = tmpdir
    app.singleSaveFile = tmpdir
    app.FileLabelName = "Sample"
    app.csvFile = "Table001.csv"
    app.BinaryImage = np.array([[0, 255],
                                [255, 0]], dtype=np.uint8)  # 2x2, two white pixels
    sz = Box(); sz.Value = 2.0  # image size in mm (assumes square)
    app.RealImageSizemm = sz
    app.biomarkers = {"nodes": 0}
    app.biomarkers_counter = 0
    app.biomarkers_cumulative = []
    app.VesselAreaDensityLabel   = make_label()
    app.VesselLengthDensityLabel = make_label()
    app.MeanDiameterLabel        = make_label()
    app.MedianDiameterLabel      = make_label()
    app.BranchpointDensityLabel  = make_label()
    return app


def main():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "CSVs"), exist_ok=True)

        # minimal CSV with 21 columns (we use 3, 19, 21)
        data = np.zeros((2, 21), float)
        data[:, 2]  = [1.0, 2.0]   # diameter (px)
        data[:, 18] = [3.0, 5.0]   # length (px)
        data[:, 20] = [1.2, 0.8]   # tortuosity
        pd.DataFrame(data).to_csv(os.path.join(tmp, "CSVs", "Table001.csv"),
                                  header=False, index=False)

        app = build_app(tmp)

        compute_biomarkers(app, Batch=True)  # avoid plotting

        # expected numbers (pix_to_mm = 2.0/2 = 1.0)
        vad = (np.sum(app.BinaryImage) / 255.0) / app.BinaryImage.size  # 0.5
        total_len = 3.0 + 5.0  # 8.0 mm
        vld = total_len / (app.RealImageSizemm.Value ** 2)  # 8 / 4 = 2.0
        diams_um = np.array([1000.0, 2000.0])  # microns
        mean_d = diams_um.mean()  # 1500.0
        median_d = np.median(diams_um)  # 1500.0
        bd0 = 0.0  # nodes=0

        # arrays written
        assert np.allclose(app.biomarkers["Diams"], diams_um)
        assert np.allclose(app.biomarkers["Lengths"], np.array([3.0, 5.0]))
        assert np.allclose(app.biomarkers["Tort"], np.array([1.2, 0.8]))

        # scalar biomarkers
        assert np.isclose(app.biomarkers["VAD"], vad)
        assert np.isclose(app.biomarkers["totalLength"], total_len)
        assert np.isclose(app.biomarkers["VLD"], vld)
        assert np.isclose(app.biomarkers["MeanDiam"], mean_d)
        assert np.isclose(app.biomarkers["MedianDiam"], median_d)
        assert np.isclose(app.biomarkers["BD"], bd0)

        # labels contain expected prefixes
        assert app.VesselAreaDensityLabel.Text.startswith("Vessel Area Density = ")
        assert app.VesselLengthDensityLabel.Text.startswith("Vessel Length Density = ")
        assert app.MeanDiameterLabel.Text.startswith("Mean Diameter = ")
        assert app.MedianDiameterLabel.Text.startswith("Median Diameter = ")
        assert app.BranchpointDensityLabel.Text.startswith("Branchpoint Density = ")

        # cumulative updated
        assert app.biomarkers_counter == 1
        assert len(app.biomarkers_cumulative) == 1
        assert app.biomarkers_cumulative[0]["name"] == "Sample"

        # rerun with nodes=2 to validate BD = 2 / total_len
        app.biomarkers["nodes"] = 2
        compute_biomarkers(app, Batch=True)
        assert np.isclose(app.biomarkers["BD"], 2.0 / total_len)
        assert app.biomarkers_counter == 2
        assert len(app.biomarkers_cumulative) == 2

    print("OK")


if __name__ == "__main__":
    main()
