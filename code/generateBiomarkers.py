from typing import Any
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_biomarkers(app: Any, Batch: bool) -> None:
    if Batch:
        dir_path = app.batchSaveFile  # dir = app.batchSaveFile
        app.biomarkers['name'] = app.FileLabelName  # app.biomarkers.name = app.FileLabelName
    else:
        dir_path = app.singleSaveFile  # dir = app.singleSaveFile

    app.biomarkers['name'] = app.FileLabelName  # repeat assignment as in MATLAB

    app.csvFile = str(app.csvFile)  # app.csvFile = char(app.csvFile)
    if not app.csvFile.endswith('v'):
        app.csvFile = app.csvFile[:-1]  # if ~(app.csvFile(end) == 'v') then trim last char

    inds = app.csvFile.find('Table')  # inds = strfind(app.csvFile,'Table')
    inds2 = app.csvFile.find('.')  # inds2 = strfind(app.csvFile,'.')
    if inds != -1 and inds2 != -1 and inds2 > inds + 6:
        imgnum = app.csvFile[inds + 6:inds2]  # imgnum = app.csvFile(inds+6:inds2-1)
    else:
        imgnum = ''
    if imgnum:  # if ~isempty(imgnum)
        imgnum = f"-{imgnum}"  # imgnum = ['-' imgnum ]

    Nx, _ = app.BinaryImage.shape  # [Nx, ~] = size(app.BinaryImage)
    pix_to_mm = app.RealImageSizemm.Value / Nx  # assumes square image

    diam_table_path = os.path.join(dir_path, 'CSVs', app.csvFile)  # DiamTableFile = [dir '\CSVs\' app.csvFile]
    if app.csvFile.lower().endswith('.csv'):
        DiamTable = pd.read_csv(diam_table_path, header=None).to_numpy()  # xlsread for CSV
    else:
        DiamTable = pd.read_excel(diam_table_path, header=None).to_numpy()  # xlsread for Excel

    app.biomarkers['Diams'] = (DiamTable[:, 2] * pix_to_mm * 1000)  # rmmissing later via numpy ops
    app.biomarkers['Diams'] = app.biomarkers['Diams'][~np.isnan(app.biomarkers['Diams'])]  # rmmissing
    app.biomarkers['Tort'] = DiamTable[:, 20]
    app.biomarkers['Tort'] = app.biomarkers['Tort'][~np.isnan(app.biomarkers['Tort'])]  # rmmissing
    app.biomarkers['Lengths'] = DiamTable[:, 18] * pix_to_mm  # in mm
    app.biomarkers['Lengths'] = app.biomarkers['Lengths'][~np.isnan(app.biomarkers['Lengths'])]  # rmmissing

    # ROI reading & node counting is commented out in MATLAB; keep it disabled here.

    app.biomarkers['VAD'] = np.sum(app.BinaryImage) / 255.0 / app.BinaryImage.size  # Vessel Area Fraction
    app.biomarkers['totalLength'] = np.sum(app.biomarkers['Lengths'])  # in mm
    app.biomarkers['VLD'] = app.biomarkers['totalLength'] / (app.RealImageSizemm.Value ** 2)  # in 1/mm
    app.biomarkers['MeanDiam'] = np.mean(app.biomarkers['Diams'])  # in microns
    app.biomarkers['MedianDiam'] = np.median(app.biomarkers['Diams'])
    app.biomarkers['BD'] = np.divide(  # Branchpoint density (use numpy divide to mirror MATLAB Inf on zero)
        app.biomarkers['nodes'], app.biomarkers['totalLength']
    )

    app.VesselAreaDensityLabel.Text = f"Vessel Area Density = {app.biomarkers['VAD']}"  # display text
    app.VesselLengthDensityLabel.Text = f"Vessel Length Density = {app.biomarkers['VLD']} (1/mm)"
    app.MeanDiameterLabel.Text = f"Mean Diameter = {app.biomarkers['MeanDiam']} µm"
    app.MedianDiameterLabel.Text = f"Median Diameter = {app.biomarkers['MedianDiam']} µm"
    app.BranchpointDensityLabel.Text = f"Branchpoint Density = {app.biomarkers['BD']} (1/mm)"

    if not Batch:
        plt.figure(); plt.hist(app.biomarkers['Diams'], bins=np.arange(0, np.max(app.biomarkers['Diams']) + 10, 10)); plt.title('Diameter Distribution'); plt.tight_layout(); plt.show()  # BinWidth=10
        plt.figure(); plt.hist(app.biomarkers['Tort'], bins=np.arange(np.min(app.biomarkers['Tort']), np.max(app.biomarkers['Tort']) + 0.1, 0.1)); plt.title('Tortuosity Distribution'); plt.tight_layout(); plt.show()  # BinWidth=0.1
        plt.figure(); plt.hist(app.biomarkers['Lengths'], bins=np.arange(np.min(app.biomarkers['Lengths']), np.max(app.biomarkers['Lengths']) + 0.1, 0.1)); plt.title('Length Distribution'); plt.tight_layout(); plt.show()  # BinWidth=0.1

    app.biomarkers_counter = app.biomarkers_counter + 1  # increment
    app.biomarkers_cumulative.append({  # store cumulative entry
        'name': app.biomarkers['name'],
        'nodes': app.biomarkers['nodes'],
        'VAD': app.biomarkers['VAD'],
        'totalLength': app.biomarkers['totalLength'],
        'VLD': app.biomarkers['VLD'],
        'MeanDiam': app.biomarkers['MeanDiam'],
        'MedianDiam': app.biomarkers['MedianDiam'],
        'BD': app.biomarkers['BD'],
    })
