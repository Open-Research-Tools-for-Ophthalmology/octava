# Author: Dylan Muir <dylan.muir@unibas.ch>
# Created: 9th August, 2011
# 
# 20170118 Added code to read slice position for point ROIs
# 20141020 Added code to read 'header 2' fields; thanks to Luca Nocetti
# 20140602 Bug report contributed by Samuel Barnes and Yousef Mazaheri
# 20110810 Bug report contributed by Jean-Yves Tinevez
# 20110829 Bug fix contributed by Benjamin Ricca <ricca@berkeley.edu>
# 20120622 Order of ROIs in a ROI set is now preserved
# 20120703 Different way of reading zip file contents guarantees that ROI order
#           is preserved
# 
# Copyright (c) 2011, 2012, 2013, 2014, 2015, 2016 Dylan Muir <dylan.muir@unibas.ch>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


''' 
COMMENTS:
- I am not sure when this function is used. OCTAVA supports user defined ROIs using matlab 
tools and a separate GUI, but it seems it can also support uploading ROIs straight from 
Image J. I'll look into this later
'''


import os
import struct
import numpy as np
import tempfile
import shutil
import zipfile

from typing import Union, List, Dict

def read_imagej_roi(filenames: Union[str, List[str]]) -> Union[Dict, List[Dict]]:
    """
    Read an ImageJ ROI (.roi file or .zip archive)
    Returns a dict (single ROI) or list of dicts (multiple ROIs)
    """
    if isinstance(filenames, list):
        # Multiple files, read each recursively (not sure if it's fastest)
        return [read_imagej_roi(f) for f in _cell_flatten(filenames)]
    else:
        filename = filenames

    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext == ".zip":
        # ROI ZIP archive: unzip, parse each .roi file, remove temp dir
        tempdir = tempfile.mkdtemp()
        with zipfile.ZipFile(filename, 'r') as zf:
            roi_files = [f for f in zf.namelist() if f.lower().endswith('.roi') and not f.startswith('__MACOSX')]
            zf.extractall(path=tempdir, members=roi_files)
        roi_paths = [os.path.join(tempdir, f) for f in roi_files]
        rois = [read_imagej_roi(f) for f in roi_paths]
        shutil.rmtree(tempdir)
        return rois

    # --- Single ROI file below this line ---

    if not os.path.exists(filename):
        raise FileNotFoundError(f"The file {filename} was not found.")

    with open(filename, "rb") as fid:
        # Check for Iout magic header
        magic = fid.read(4).decode("ascii")
        if magic != "Iout":
            raise ValueError(f"File {filename} is not an ImageJ ROI file.")
        roi = {}

        # Read Version (big-endian short)
        roi['nVersion'], = struct.unpack('>h', fid.read(2))

        # ROI type (byte), skip 1 byte
        nTypeID, = struct.unpack('>B', fid.read(1))
        fid.read(1)

        # Rectangular bounds (TLBR, 4 shorts)
        vnRectBounds = struct.unpack('>hhhh', fid.read(8))
        roi['vnRectBounds'] = np.array(vnRectBounds)
        # Number of coordinates (ushort)
        nNumCoords, = struct.unpack('>H', fid.read(2))

        # Read the rest of the header that is required for cases
        vfLinePoints = struct.unpack('>4f', fid.read(16))
        nStrokeWidth, = struct.unpack('>h', fid.read(2))
        nShapeROISize, = struct.unpack('>I', fid.read(4))
        nStrokeColor, = struct.unpack('>I', fid.read(4))
        nFillColor, = struct.unpack('>I', fid.read(4))
        nROISubtype, = struct.unpack('>h', fid.read(2))
        nOptions, = struct.unpack('>h', fid.read(2))
        nArrowStyle = struct.unpack('>B', fid.read(1))[0]
        nArrowHeadSize = struct.unpack('>B', fid.read(1))[0]
        nRoundedRectArcSize, = struct.unpack('>h', fid.read(2))
        nPosition, = struct.unpack('>I', fid.read(4))

        # Save for later use
        roi['_header_params'] = dict(
            vfLinePoints=vfLinePoints, nStrokeWidth=nStrokeWidth,
            nShapeROISize=nShapeROISize, nStrokeColor=nStrokeColor, nFillColor=nFillColor,
            nROISubtype=nROISubtype, nOptions=nOptions, nArrowStyle=nArrowStyle,
            nArrowHeadSize=nArrowHeadSize, nRoundedRectArcSize=nRoundedRectArcSize, nPosition=nPosition,
            nNumCoords=nNumCoords
        )

        # Header 2 offset (used for version >= 218 and position etc.)
        nHeader2Offset, = struct.unpack('>I', fid.read(4))

        # If there is header2, read positions etc.
        vnPosition = None
        vnNameParams = (0, 0)
        nCountersOffset = 0
        if nHeader2Offset > 0:
            try:
                fid.seek(nHeader2Offset+4)
                vnPosition = struct.unpack('>3I', fid.read(12))
                vnNameParams = struct.unpack('>2I', fid.read(8))
                # the following aren't used but could be read as per .m code
                fid.read(4)      # skip nOverlayLabelColor (uint32)
                fid.read(2)      # skip nOverlayFontSize (int16)
                fid.read(1)      # skip 1
                fid.read(1)      # skip nOpacity (uint8)
                fid.read(4)      # skip nImageSize (uint32)
                fid.read(4)      # skip fStrokeWidth (float32)
                fid.read(8)      # skip vnROIPropertiesParams (2 x uint32)
                nCountersOffset, = struct.unpack('>I', fid.read(4))
                vnPosition = np.array(vnPosition)
            except Exception as e:
                # fallback if not enough header...
                vnPosition = None
                vnNameParams = (0, 0)
                nCountersOffset = 0

        else:
            vnPosition = None
            vnNameParams = (0, 0)
            nCountersOffset = 0

        roi['vnPosition'] = vnPosition if vnPosition is not None else []
        
        # ROI name: try to read from header, or fallback to basename
        if not vnNameParams or vnNameParams[0] == 0 or vnNameParams[1] == 0:
            roi['strName'] = os.path.splitext(os.path.basename(filename))[0]
        else:
            fid.seek(vnNameParams[0])
            roi['strName'] = fid.read(2 * vnNameParams[1]).decode('utf-16-be')

        # Get aspect ratio (f32 at offset 52)
        fid.seek(52)
        fAspectRatio, = struct.unpack('>f', fid.read(4))

        fid.seek(64)
        
        # ----- Now parse according to ROI type (dispatch) ------
        # We'll call helper functions for each ROI type
        roi = _parse_roi_type(fid, nTypeID, roi, filename, nNumCoords, nROISubtype, nOptions,
                              nRoundedRectArcSize, nShapeROISize, fAspectRatio, vfLinePoints,
                              nCountersOffset)
        # Handle v218+ (strokewidth/colors/text) etc
        if roi['nVersion'] >= 218:
            roi['nStrokeWidth'] = nStrokeWidth
            roi['nStrokeColor'] = nStrokeColor
            roi['nFillColor'] = nFillColor
            roi['bSplineFit'] = bool(nOptions & 1)
            if nROISubtype == 1:
                # Text ROI (see .m code)
                fid.seek(64)
                roi['nFontSize'], = struct.unpack('>I', fid.read(4))
                roi['nFontStyle'], = struct.unpack('>I', fid.read(4))
                nNameLength, = struct.unpack('>I', fid.read(4))
                nTextLength, = struct.unpack('>I', fid.read(4))
                roi['strFontName'] = fid.read(nNameLength * 2).decode('utf-16-be')
                roi['strText'] = fid.read(nTextLength * 2).decode('utf-16-be')
        # Done
        return roi

def _cell_flatten(lst):
    """
    Recursively flattens a list of possibly-nested lists into a flat list.
    """
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(_cell_flatten(item))
        else:
            result.append(item)
    return result

def _parse_roi_type(fid, nTypeID, roi, filename, nNumCoords, nROISubtype, nOptions,
                    nRoundedRectArcSize, nShapeROISize, fAspectRatio, vfLinePoints,
                    nCountersOffset):
    """
    Helper to handle specific ROI types
    """
    bOpt_SubPixelResolution = 128

    # Helper for reading X/Y/Counter coordinates
    def read_coordinates():
        if nOptions & bOpt_SubPixelResolution:
            # Subpixel: seek to 64 + 4*nNumCoords
            fid.seek(64 + 4 * nNumCoords, 0)
            x = np.frombuffer(fid.read(nNumCoords*4), dtype='>f4')
            y = np.frombuffer(fid.read(nNumCoords*4), dtype='>f4')
        else:
            x = np.frombuffer(fid.read(nNumCoords*2), dtype='>i2')
            y = np.frombuffer(fid.read(nNumCoords*2), dtype='>i2')
            # below: offset x/y by top/left, trim <0 to 0
            x = np.where(x < 0, 0, x)
            y = np.where(y < 0, 0, y)
            x = x + roi['vnRectBounds'][1]
            y = y + roi['vnRectBounds'][0]
        coords = np.stack([x, y], axis=-1)
        vnCounters = None
        if nCountersOffset:
            fid.seek(nCountersOffset)
            vnCounters = np.frombuffer(fid.read(nNumCoords*4), dtype='>u4')
        return coords, vnCounters

    # Type dispatch
    if nTypeID == 1:         # Rectangle
        roi['strType'] = "Rectangle"
        roi['nArcSize'] = nRoundedRectArcSize
        if nShapeROISize > 0:
            roi['strSubtype'] = 'Shape'
            # Unclear: in MATLAB code, it's a vector of nShapeROISize float32s
            roi['vfShapes'] = np.frombuffer(fid.read(nShapeROISize*4), dtype='>f4')
    elif nTypeID == 2:       # Oval
        roi['strType'] = "Oval"
    elif nTypeID == 3:       # Line
        roi['strType'] = "Line"
        roi['vnLinePoints'] = np.round(np.array(vfLinePoints)).astype(int)
        if nROISubtype == 2:
            roi['strSubtype'] = "Arrow"
            roi['bDoubleHeaded'] = bool(nOptions & 2)
            roi['bOutlined'] = bool(nOptions & 4)
            roi['nArrowStyle'] = roi['_header_params']['nArrowStyle']
            roi['nArrowHeadSize'] = roi['_header_params']['nArrowHeadSize']
    elif nTypeID == 0:       # Polygon
        roi['strType'] = "Polygon"
        roi['mnCoordinates'], _ = read_coordinates()
    elif nTypeID == 7:       # Freehand
        roi['strType'] = "Freehand"
        roi['mnCoordinates'], _ = read_coordinates()
        if nROISubtype == 3:
            roi['strSubtype'] = "Ellipse"
            roi['vfEllipsePoints'] = np.array(vfLinePoints)
            roi['fAspectRatio'] = fAspectRatio
    elif nTypeID == 8:       # Traced
        roi['strType'] = "Traced"
        roi['mnCoordinates'], _ = read_coordinates()
    elif nTypeID == 5:       # PolyLine
        roi['strType'] = "PolyLine"
        roi['mnCoordinates'], _ = read_coordinates()
    elif nTypeID == 4:       # FreeLine
        roi['strType'] = "FreeLine"
        roi['mnCoordinates'], _ = read_coordinates()
    elif nTypeID == 9:       # Angle
        roi['strType'] = "Angle"
        roi['mnCoordinates'], _ = read_coordinates()
    elif nTypeID == 10:      # Point
        roi['strType'] = "Point"
        coords, vnCounters = read_coordinates()
        roi['mfCoordinates'] = coords
        if vnCounters is None:
            roi['vnCounters'] = np.zeros(nNumCoords, dtype=int)
            roi['vnSlices'] = np.ones(nNumCoords, dtype=int)
        else:
            roi['vnCounters'] = np.bitwise_and(vnCounters, 255)
            roi['vnSlices'] = np.right_shift(vnCounters, 8)
    elif nTypeID == 6:       # NoROI
        roi['strType'] = "NoROI"
    else:
        raise ValueError(f"ROI file {filename} contains unknown ROI type {nTypeID}")
    return roi
