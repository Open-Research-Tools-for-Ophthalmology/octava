

<div align="center">
  <h3>
    OCTAVA
  </h3>

  ![PyPI - License](https://img.shields.io/badge/license-MIT-blue)
</div>

This respoitory contains all the sourcecode required to run the OCTAVA software OCTAVA is available free for use under an MIT licence. If you use this software in your research, please cite the following papers:

xxx. https://doi.org/xxx/xxx

![](assets/doc_images/gui.png)
| _`OCTAVA` processing OCTA images with binarisation, skeletaization, FAZ segmentation and microvascular analysis_

# Quick Start
Find the latest distrbution in the [releases](https://github.com/milanaveed/octava/releases) page that is suitable for your Operating System (Windows/MacOS/Linux) and Hardware Architecture (x86_64/arm64). 

Some distributions are not available due to limited resources, in this case you can try to install on your own by following the guide down below.

## Installation
Install python [3.10.19](https://www.python.org/downloads/release/python-31019/) or later versions. 
Once installed, run the following command with pip to install necessary packages:
```
pip install -r requirements.txt
```
**For Conda Users:** ```conda env create -f environment.yml```\
(update as often as possible)

## Start the App
Run ```python gui/build/gui.py``` to launch the application






## Set-up
Hi everyone, welcome to the repository, please clone the repository to your device first. When developing, please create a new feature branch from `main`. Before you resume your work, run `git pull origin main` to download updates from `main` to your feature branch. And when creating pull requests, merge your feature branch into `main`. 

Source code is placed under the folder `source` for the ease of development (please try not to change the source files), please place our Python code in the folder `code`.

One example:
If you’re working on a new feature or fix:
- You should base your work on main.
- Therefore, fetch from origin and create your new feature branch.
```
git fetch origin
git checkout main
git pull origin main   # updates your local main
git checkout -b feature/your-feature-name
```

## Environment
If you use Conda, you can recreate the coding environment for this repository by using `conda env create -f environment.yml -n octava`.

## Note
The slicing differences between Python and Matlab:
- In MATLAB, 1:m includes the m-th element; index starts at 1.
- In Python, 0:m includes up to m-1; index starts at 0.


## Meetings
### 17 Nov
1. automatic faz: (Laura's code)
2. image resize (upscaling the image so kernel sizes of filters will work) (if hard coded, no need to do batch resize in batch processing settings)
3. add kernel size field to median filter
4. (optional) for regional analysis, identify if the centre has shifted
5. point faz: Use raw image not the binarised image to draw the contour.
6. use the circle movement for optic nerve head


- regional analysis: nasal and temporal
```
%Set max values for kernel size for median filter, frangi
            %filter, and adaptive thresholding to the image size 
            app.kernelSize.Limits = [0 app.fullImSizePix(1)]; 
            app.sigmamaxSpinner.Limits = [0 app.fullImSizePix(1)]; 
            app.ATkernelsizeSpinner.Limits = [0 app.fullImSizePix(1)];
```