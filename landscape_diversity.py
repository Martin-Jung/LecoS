# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LecoS
                                 A QGIS plugin
 Contains analytical functions for landscape analysis
                             -------------------
        begin                : 2012-09-06
        copyright            : (C) 2012 by Martin Jung
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
# Import PyQT bindings
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect

# Import numpy and scipy
import numpy
try:
    import scipy
except ImportError:
    QMessageBox.warning(QDialog(),"LecoS: Warning","Please install scipy (http://scipy.org/) in your QGIS python path.")
    sys.exit(0)
from scipy import ndimage # import ndimage module seperately for easy access

# Try to import functions from osgeo
try:
    from osgeo import gdal
except ImportError:
    import gdal
try:
    from osgeo import ogr
except ImportError:
    import ogr
try:
    from osgeo import osr
except ImportError:
    import osr
try:
    from osgeo import gdal_array
except ImportError:
    import gdalnumeric
try:
    from osgeo import gdalconst
except ImportError:
    import gdalconst
    
# Register gdal and ogr drivers
if hasattr(gdal,"AllRegister"): # Can register drivers
    gdal.AllRegister() # register all gdal drivers
if hasattr(ogr,"RegisterAll"):
    ogr.RegisterAll() # register all ogr drivers

# Try to use exceptions with gdal and ogr
if hasattr(gdal,"UseExceptions"):
    gdal.UseExceptions()
if hasattr(ogr,"UseExceptions"):
    ogr.UseExceptions()

helpdir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/LecoS/metric_info/"
tmpdir = tempfile.gettempdir()

## CODE START ##
# Diversity Indices
# Returns different diversity indices for the whole landscape with exception of no_data_values
class LandscapeDiversity():
    def __init__(self,rasterPath):
        self.rasterPath = rasterPath
        
        # Preprocessing
        self.raster = gdal.Open(str(self.rasterPath))
        band = self.raster.GetRasterBand(1)
        self.nodata = band.GetNoDataValue()
        try:
            self.array =  band.ReadAsArray()
        except ValueError:
            QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
            return
        self.classes = sorted(numpy.unique(self.array)) # get classes
        self.classes.remove(self.nodata) # Remove nodata value from class list
        
    # Calculates a Diversity Index    
    def f_returnDiversity(self,index):
        if(index=="shannon"):
            sh = []
            cl_array = numpy.copy(self.array) # create working array
            cl_array[cl_array==int(self.nodata)] = 0
            for cl in self.classes:
                res = []
                for i in self.classes:
                    arr = numpy.copy(self.array)
                    arr[self.array!=i] = 0
                    res.append(numpy.count_nonzero(arr))
                arr = numpy.copy(self.array)
                arr[self.array!=cl] = 0
                prop = numpy.count_nonzero(arr) / float(sum(res))
                sh.append(prop * math.log(prop))
            return sum(sh)*-1
        elif(index=="simpson"):
            si = []
            cl_array = numpy.copy(self.array) # create working array
            cl_array[cl_array==int(self.nodata)] = 0
            for cl in self.classes:
                res = []
                for i in self.classes:
                    arr = numpy.copy(self.array)
                    arr[self.array!=i] = 0
                    res.append(numpy.count_nonzero(arr))
                arr = numpy.copy(self.array)
                arr[self.array!=cl] = 0
                prop = numpy.count_nonzero(arr) / float(sum(res))
                si.append(math.pow(prop,2))
            return 1-sum(si)
        elif(index=="eveness"):
            return self.f_returnDiversity("shannon") / math.log(len(self.classes))
        else:
            print "Diversity Index not available (yet)"
    
    def testing_def(self):
        ####
        import numpy
        from scipy import ndimage
        import matplotlib.pyplot as plt
        
        rasterPath = "/home/martin/Science/Bialowieza_TestData/fc_raster_plot23.tif"
        raster = gdal.Open(str(rasterPath))
        array = raster.GetRasterBand(1).ReadAsArray()
        
        plt.imshow(array)
        plt.axis('on')
        plt.show()

        a = numpy.zeros((6,6), dtype=numpy.int) 
        a[1:5, 1:5] = 1;a[3,3] = 0 ; a[2,2] = 2

        s = ndimage.generate_binary_structure(2,2) # Binary structure
        #.... Calculate Sum of 
        b = a[1:-1, 1:-1]
        print(numpy.exp(ndimage.convolve(numpy.log(b), s, mode = 'constant')))
        result_array = numpy.zeros_like(a)