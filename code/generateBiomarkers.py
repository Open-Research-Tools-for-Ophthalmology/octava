from typing import Any
import os
import numpy as np
import pandas as pd
import zipfile
import matplotlib.pyplot as plt

def compute_biomarkers(app: Any, Batch: bool) -> None:
    """
    Compute a series of vascular biomarkers from the provided image data,
    update the application state, and display results in the UI.

    Parameters
    ----------
    app : Any
        The application object providing:
        - batchSaveFile or singleSaveFile paths
        - csvFile and FileLabelName attributes
        - BinaryImage (numpy array) and RealImageSizemm.Value for scaling
        - biomarkers (dict), biomarkers_counter (int), biomarkers_cumulative (list)
        - UI labels for displaying results (e.g., VesselAreaDensityLabel.Text)
    Batch : bool
        If True, process a batch directory; otherwise, process a single file.

    Returns
    -------
    None
    """
    # File Path Selection and Initialization
    dir_path = app.batchSaveFile if Batch else app.singleSaveFile
    app.biomarkers['name'] = app.FileLabelName

    # Process the CSV file name
    csv_file = str(app.csvFile)
    if not csv_file.endswith('v'):
        csv_file = csv_file[:-1]  # Remove last character if it's not 'v'

    # Extract image number suffix from the filename
    imgnum = ''
    if 'Table' in csv_file and '.' in csv_file:
        start = csv_file.index('Table') + len('Table')
        end = csv_file.rindex('.')
        num = csv_file[start:end]
        if num:
            imgnum = f"-{num}"

    # Pixel to Millimeter Conversion
    Nx, _ = app.BinaryImage.shape
    pix_to_mm = app.RealImageSizemm.Value / Nx

    # Reading Excel Table and Converting Units
    diam_table_path = os.path.join(dir_path, 'CSVs', csv_file)
    diam_df = pd.read_excel(diam_table_path, header=None)
    diams   = (diam_df.iloc[:,  2] * pix_to_mm * 1000).dropna().to_numpy()  # in microns
    tort    = (diam_df.iloc[:, 20]).dropna().to_numpy()
    lengths = (diam_df.iloc[:, 18] * pix_to_mm).dropna().to_numpy()  # in mm

    app.biomarkers.update({
        'Diams':   diams,
        'Tort':    tort,
        'Lengths': lengths,
    })

    # Read ROIS to count nodes, Still not 100% sure this is correct - need to double check
    roi_zip = os.path.join(
        dir_path,
        'ROIs',
        f"{app.FileLabelName}_Network-RoiSet{imgnum}.zip"
    )
    nodes = 0
    if os.path.exists(roi_zip):
        with zipfile.ZipFile(roi_zip, 'r') as zf:
            for name in zf.namelist():
                if 'junction' in name or 'node' in name:
                    nodes += 1
    app.biomarkers['nodes'] = nodes

    # Calculate biomarkers
    VAD          = np.sum(app.BinaryImage) / 255.0 / app.BinaryImage.size  # Vessel Area Density
    total_length = np.sum(lengths)
    VLD          = total_length / (app.RealImageSizemm.Value ** 2)         # Vessel Length Density
    mean_diam    = np.mean(diams)
    median_diam  = np.median(diams)
    BD           = nodes / total_length if total_length != 0 else 0        # Branchpoint Density

    app.biomarkers.update({
        'VAD':         VAD,
        'totalLength': total_length,
        'VLD':         VLD,
        'MeanDiam':    mean_diam,
        'MedianDiam':  median_diam,
        'BD':          BD,
    })

    # Display results - calculated biomarkers
    app.VesselAreaDensityLabel.Text    = f"Vessel Area Density = {VAD:.4f}"
    app.VesselLengthDensityLabel.Text  = f"Vessel Length Density = {VLD:.4f} (1/mm)"
    app.MeanDiameterLabel.Text         = f"Mean Diameter = {mean_diam:.2f} µm"
    app.MedianDiameterLabel.Text       = f"Median Diameter = {median_diam:.2f} µm"
    app.BranchpointDensityLabel.Text   = f"Branchpoint Density = {BD:.4f} (1/mm)"

    # Will using histogram vs hist cause an issue with non-uniform, bin size between datasets? Need to check this!
    if not Batch:
        fig, axes = plt.subplots(3, 1, figsize=(6, 8))
        axes[0].hist(diams, bins=np.arange(0, diams.max()+10, 10))
        axes[0].set_title('Diameter Distribution')
        axes[1].hist(tort, bins=np.arange(tort.min(), tort.max()+0.1, 0.1))
        axes[1].set_title('Tortuosity Distribution')
        axes[2].hist(lengths, bins=np.arange(lengths.min(), lengths.max()+0.1, 0.1))
        axes[2].set_title('Length Distribution')
        plt.tight_layout()
        plt.show()

    # Store biomarkers in cumulative list
    app.biomarkers_counter += 1
    entry = {
        'name':         app.biomarkers['name'],
        'nodes':        nodes,
        'VAD':          VAD,
        'totalLength':  total_length,
        'VLD':          VLD,
        'MeanDiam':     mean_diam,
        'MedianDiam':   median_diam,
        'BD':           BD,
    }
    app.biomarkers_cumulative.append(entry)
