# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LecoS
                                 A QGIS plugin
 Contains analytical functions for landscape analysis
                             -------------------
        begin                : 2012-09-06
        copyright            : (C) 2013 by Martin Jung
        email                : martinjung@zoho.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

import gdal, numpy, sys, scipy, string, math, ogr, os
import subprocess
import tempfile
from scipy import ndimage
try:
    gdal.AllRegister() # register all gdal drivers
    gdal.UseExceptions()
    ogr.UseExceptions()
except AttributeError:
    #QMessageBox.warning(QDialog(),"LecoS: Warning","The gdal driver register command failed. LecoS might still work, but there is a chance of non working gdal file support.")
    
tmpdir = tempfile.gettempdir()

#Teststuff
rasterPath = "/home/martin/Science/Bialowieza_TestData/fc_raster.tif"

# load as a gdal image to get geotransform and full array
srcImage = gdal.Open(str(rasterPath))
try:
    array = srcImage.GetRasterBand(1).ReadAsArray() # Convert first band to array
except ValueError:
    QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
    return

import matplotlib.pyplot as plt
plt.imshow(edge,interpolation='nearest')
plt.axis('on')
plt.show()

s = ndimage.generate_binary_structure(2,2)
classes = sorted(numpy.unique(array)) # get classes
nodata = srcImage.GetRasterBand(1).GetNoDataValue()
classes.remove(nodata)

cl_array = numpy.copy(array)
cl_array[array!=1] = 0

labeled_array, numpatches = ndimage.label(cl_array,s)
e = numpy.zeros(cl_array.shape)

b = ndimage.binary_dilation(cl_array.astype(int),s)
b = ndimage.binary_closing(cl_array,s,3)

edge = ndimage.distance_transform_cdt(b == 0) == 1

cm = ndimage.center_of_mass(cl_array,labeled_array,range(numpatches + 1))

print cl_array[cm[1][0],cm[1][1]]
plt.imshow(cl_array[cm[1][0],cm[1][1]],interpolation='nearest')
plt.axis('on')
plt.show()
