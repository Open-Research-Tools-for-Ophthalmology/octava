# Overview
This pipeline accepts a greyscale OCTA image and its corresponding binary FAZ mask, performs automated FAZ segmentation and compares the predictions to the GT mask. The following metrics are calculated:
 - Dice
 - Jaccard's Index (IOU)
 - Precision
 - Recall
 - Area Difference (%)
 - Predicted FAZ
    - Area (px<sup>2</sup>)
    - Perimeter (px)
    - Area (mm<sup>2</sup>)
    - Perimeter (mm)
    - Acircularity
    - Circularity

# Installation
## Create a virtual environment
This pipeline was developed with Python 3.10.18. If this version of Python is installed on the machine, you can use `venv`. Else, `pyenv` is recommended

### venv:
Create a new virtual environment named `myenv`
```sh
python3.10 -m venv myenv
```
To activate this venv, on macOS/Linux:
```sh
source myenv/bin/activate
```
on Windows:
```sh
myenv\Scripts\activate
```
The shell prompt should now begin with the name of your virtual environment to signify you are operating in the virtual environment
```sh
(myenv)
```

### pyvenv:
If you do not have Python 3.10.18 installed, you can install the `pyenv` package and install a virtual environment with a specific Python version
```sh
pyenv install 3.10.18
```
Move into the `faz-seg` directory, activate the virtual environment with
```sh
pyenv local 3.10.18
```
To verify this has succeeded, the following command will return the active Python version
```sh
pyenv local
```

## Install dependencies
Run this command to install the required packages in the virtual environment
```sh
pip install -r requirements.txt
```

# Run the pipeline
## Single segmentation
This is the default mode of the pipeline, this requires no flags to specify so. Within the `config.yml` file, `filepath`, `gt_filepath`, and `scan_size` should be specified according to the path to the image to be segmented and scan size. These filepaths should be relative to the `datasets` folder. Segmentation metrics will be printed out in the terminal window. 

## Batch segmentation
Edit the `config.yml` file to specify path to the folder of images to be segmented, their corresponding GT mask and scan size. There should be some naming convention for the images and their GT masks, e.g. image1.png has a mask named image1_mask.png. `gt_suffix` in `config.yml` should be updated to follow this convention.

Batch mode requires the `--batch` flag and `--output` flag to specify the name of the batch job. The results of the batch job are saved in the `batch` folder. The outputs are a csv file of results (`out.csv`) as well as a summary file that calculates the mean, std dev and median of the results (`summary.txt`).

```
batch/ 
└── job_name/
    ├── out.csv
    └── summary.txt
```

Verbose segmentation with `--steps` and `--candidate` is available in batch mode but not recommended.

## Flags
To facilitate, step-by-step analysis of the segmentation process, the following flags can also be enabled:
 - `--steps` \
    Throughout each step of the pipeline, displays the original image inputted, results of the previous and current step for visual inspection. This also enables the `candidate` flag
- `candidate` \
    Displays the FAZ candidates considered during segmentation, their metrics and score

## Examples
Batch job named job1
```sh
python main.py --batch --output job1
```
Segmenting a single image
```sh
python main.py
```
Segmenting a single image and comparing regions considered to be FAZ
```sh
python main.py --candidate
```


# Pack down
Once you are done running the pipeline, deactivate the virtual environment to return to your original settings
### venv:
```sh
deactivate
```

### pyenv:
```
pyenv local --unset
```
