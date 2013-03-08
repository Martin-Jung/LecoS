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
    pass
tmpdir = tempfile.gettempdir()

# Landscape Modifier class
class LandscapeMod():
    def __init__(self,rasterPath,cl):
        
        # load as a gdal image to get full array
        self.srcImage = gdal.Open(str(rasterPath))
        self.nodata = self.srcImage.GetRasterBand(1).GetNoDataValue()
        try:
            self.srcArray = self.srcImage.GetRasterBand(1).ReadAsArray() # Convert first band to array
        except ValueError:
            QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
            return
        self.cl = cl
        self.cl_array = numpy.copy(self.srcArray)
        self.cl_array[self.srcArray!=self.cl] = 0
        
        #Teststuff
#         rasterPath = "/home/martin/Projekte/Bialowieza_TestData/fc_raster.tif" #load as a gdal image to get geotransform and full array
#         srcImage = gdal.Open(str(rasterPath))
#         array = srcImage.GetRasterBand(1).ReadAsArray() # Convert first band to array
#         cl_array = numpy.copy(array)
#         cl_array[array!=1] = 0
#         s = ndimage.generate_binary_structure(2,2)
#         labeled_array, numpatches = ndimage.label(cl_array,s)
#         
#         import matplotlib.pyplot as plt
#         plt.imshow(min_feature,interpolation='nearest')
#         plt.axis('on')
#         plt.show()



    # Extract edges from landscape patches class
    def extractEdges(self,size):
        # Extract basic edge skeleton
        edge = ndimage.distance_transform_edt(self.cl_array == 0) == 1
        # Increase Size if needed
        if size > 1:
            s = ndimage.generate_binary_structure(2,1) #taxi-cab structure default
            edge = ndimage.binary_dilation(edge,s,iterations=size-1)
        return(edge)
    
    # Isolate smallest or greatest Patch from raster
    def getPatch(self,which):
        s = ndimage.generate_binary_structure(2,2) # Chessboard struct
        labeled_array, numpatches = ndimage.label(self.cl_array,s)
        sizes = ndimage.sum(self.cl_array,labeled_array,range(1,numpatches+1))

        # inside the largest, respecitively the smallest labeled patches with values
        if which == "min":
            mip = numpy.where(sizes==sizes.min())[0] + 1
            min_index = numpy.zeros(numpatches + 1, numpy.uint8)
            min_index[mip] = self.cl
            feature = min_index[labeled_array]
        else:
            map = numpy.where(sizes==sizes.max())[0] + 1 
            max_index = numpy.zeros(numpatches + 1, numpy.uint8)
            max_index[map] = self.cl
            feature = max_index[labeled_array]
        
        return(feature)
    
    # Increase or decrease landscape patches
    def InDecPatch(self,which,amount):
        s = ndimage.generate_binary_structure(2,1) # taxi-cab struct
        if which == 0:
            ras = ndimage.binary_dilation(self.cl_array,s,iterations=amount,border_value=0)
        else:
            ras = ndimage.binary_erosion(self.cl_array,s,iterations=amount,border_value=0)
        return(ras)
    
    # Close inner patch holes
    def closeHoles(self):
        s = ndimage.generate_binary_structure(2,2) # Chessboard struct
        ras = ndimage.binary_fill_holes(self.cl_array,s)
        return(ras)
    
    # Remove smaller pixels in class raster
    def cleanRaster(self,n):
        s = ndimage.generate_binary_structure(2,1) # Taxicab struct
        ras = ndimage.binary_opening(self.cl_array,s,iterations=n).astype(numpy.int)
        return(ras)
    
    