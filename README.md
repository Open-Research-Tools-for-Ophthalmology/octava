<div align="center">

# OCTAVA

[![Latest GitHub release](https://img.shields.io/github/release/Open-Research-Tools-for-Ophthalmology/octava.svg)](https://github.com/Open-Research-Tools-for-Ophthalmology/octava/releases) [![All releases](https://img.shields.io/github/downloads/Open-Research-Tools-for-Ophthalmology/octava/total.svg)](https://github.com/Open-Research-Tools-for-Ophthalmology/octava/releases) [![Issues](https://img.shields.io/github/issues/Open-Research-Tools-for-Ophthalmology/octava.svg)](https://github.com/Open-Research-Tools-for-Ophthalmology/octava/issues)[![GitHub stars](https://img.shields.io/github/stars/Open-Research-Tools-for-Ophthalmology/octava.svg)](https://github.com/Open-Research-Tools-for-Ophthalmology/octava/stargazers) [![MIT License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Open-Research-Tools-for-Ophthalmology/octava/LICENSE)

</div>

This repository contains all the source code required to run the OCTAVA software. OCTAVA is available free for use under an MIT licence. If you use this software in your research, please cite the following papers:

``` 
Untracht, G. R., Durkee, M. S., Zhao, M., Kwok-Cheung Lam, A., Sikorski, B. L., Sarunic, M. V., Andersen, P. E., Sampson, D. D., Chen, F. K., & Sampson, D. M. (2024). Towards standardising retinal OCT angiography image analysis with open-source toolbox OCTAVA. Scientific reports, 14(1), 5979. https://doi.org/10.1038/s41598-024-53501-6
```

```
Untracht, G. R., Matos, R. S., Dikaios, N., Bapir, M., Durrani, A. K., Butsabong, T., Campagnolo, P., Sampson, D. D., Heiss, C., & Sampson, D. M. (2021). OCTAVA: An open-source toolbox for quantitative analysis of optical coherence tomography angiography images. PloS one, 16(12), e0261052. https://doi.org/10.1371/journal.pone.0261052
```

![](assets/doc_images/gui.png)
| _`OCTAVA` processing OCTA images with binarisation, skeletonisation, FAZ segmentation and microvascular analysis_

# Getting Started

## Quick Download

📩 See the latest releases in the [Github Releases](https://github.com/Open-Research-Tools-for-Ophthalmology/octava/releases) page 📩.
Find the distribution that is suitable for your Operating System (Windows/MacOS/Linux) and Hardware Architecture (X86_64/Arm64).

_Some distributions (e.g. Windows/Linux on Arm64, MacOS on X86_64) are not available due to limited resources, in this case you can try to install on your own by following the guide down below._

## Build Locally

First `git clone` or download zip from this repository.

### Prerequisites

Install python [3.10.19](https://www.python.org/downloads/release/python-31019/) or compatible versions.

### One-Line Build
In your terminal, run:

```
python build_executable.py
```

## Develop Locally

For those who read source code for fun or would like to apply your own changes. The following steps describe the process for running the project locally.

Run the following command to install necessary packages:

```
pip install -r requirements.txt
```

**For Conda Users:** `conda env create -f environment.yml`\
(update as often as possible)

### Post-Installation

Run `python code/gui.py` to launch the application

### Errors

Your cache file may be corrupt/broken, try clicking the `clear` button or deleting `cache.json` to fix it