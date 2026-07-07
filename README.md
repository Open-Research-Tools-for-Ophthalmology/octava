<div align="center">

# OCTAVA

[![Latest GitHub release](https://img.shields.io/github/release/milanaveed/octava.svg)](https://github.com/milanaveed/octava/releases) [![All releases](https://img.shields.io/github/downloads/milanaveed/octava/total.svg)](https://github.com/milanaveed/octava/releases) [![Issues](https://img.shields.io/github/issues/milanaveed/octava.svg)](https://github.com/milanaveed/octava/issues)[![GitHub stars](https://img.shields.io/github/stars/milanaveed/octava.svg)](https://github.com/milanaveed/octava/stargazers) [![MIT License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/milanaveed/octava/LICENSE)

</div>

This repository contains all the source code required to run the OCTAVA software. OCTAVA is available free for use under an MIT licence. If you use this software in your research, please cite the following papers:

xxx. https://doi.org/xxx/xxx

![](assets/doc_images/gui.png)
| _`OCTAVA` processing OCTA images with binarisation, skeletonisation, FAZ segmentation and microvascular analysis_

# Getting Started

## Quick Download

📩 See the latest releases in the [Github Releases](https://github.com/milanaveed/octava/releases) page 📩.
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