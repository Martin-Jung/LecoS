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
except AttributeError:
    #QMessageBox.warning(QDialog(),"LecoS: Warning","The gdal driver register command failed. LecoS might still work, but there is a chance of non working gdal file support.")
    pass
try:
    ogr.UseExceptions()
    gdal.UseExceptions()
except AttributeError:
    pass    

helpdir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/LecoS/metric_info/"
tmpdir = tempfile.gettempdir()


# List all available landscape functions
# All defined metrics must possess an info file in the metric_info folder
def listStatistics():
    functionList = []
    
    functionList.append(unicode("Land cover")) # Calculate Area
    functionList.append(unicode("Landscape Proportion")) # Landscape Proportion
    functionList.append(unicode("Edge length")) # Calculate edge length
    functionList.append(unicode("Edge density")) # Calculate Edge Density
    functionList.append(unicode("Number of Patches")) # Return Number of Patches
    functionList.append(unicode("Patch density")) # Return Patch density
    functionList.append(unicode("Greatest patch area")) # Return Greatest Patch area
    functionList.append(unicode("Smallest patch area")) # Return Smallest Patch area
    functionList.append(unicode("Mean patch area")) # Return Mean Patch area
    functionList.append(unicode("Overall Core area")) # Return Core area
    functionList.append(unicode("Landscape division")) # Return Landscape Division Index
    functionList.append(unicode("Effective Meshsize")) # Return Effectiv Mesh Size      
    functionList.append(unicode("Splitting Index")) # Return Splitting Index
    
    return functionList

# Returns definition and reference for given function
def returnHelp(name, textfield):
    s = string.replace(name," ","_")
    h = (helpdir+s+".html")
    #textfield.setHtml(open(h).read())
    f = QFile(h)
    f.open(QFile.ReadOnly|QFile.Text)
    istream = QTextStream(f)
    textfield.setHtml(istream.readAll())
    f.close()

# Prepare raster for component labeling
def f_landcover(raster,nodata=None):
    raster = gdal.Open(str(raster))
    if(raster.RasterCount==1):
        band = raster.GetRasterBand(1)
        if nodata == None:
            nodata = band.GetNoDataValue()
        try:
            array =  band.ReadAsArray() 
        except ValueError:
            QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
            return
        classes = sorted(numpy.unique(array)) # get classes
        try:
            classes.remove(nodata)
        except ValueError:
            pass # Clipped Raster has no No-data fields, therefore nothing is removed
        return classes, array
    else:
        # TODO: Multiband Support?
        QMessageBox.warning( QDialog(),"LecoS: Warning","Multiband Rasters not implemented yet")

# Returns the nodata value. Assumes an raster with one band
def f_returnNoDataValue(rasterPath):
    raster = gdal.Open(str(rasterPath))
    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    return nodata    


class LandCoverAnalysis():
    def __init__(self,array,cellsize,classes):
        self.array = array
        self.cellsize = cellsize
        self.cellsize_2 = math.pow(cellsize,2)
        self.classes = classes
        
        # Do basic Preprocessing 
        self.f_LandscapeArea() # Calculate LArea

        
    # Executes the Metric functions
    def execSingleMetric(self,name,cl):
        self.cl = cl
        if(name == unicode("Land cover")):
            return unicode(name), self.f_returnArea(self.labeled_array)
        if(name == unicode("Landscape Proportion")):
            return unicode(name), self.f_returnProportion(self.array,cl)
        elif(name == unicode("Edge length")):
            return unicode(name), self.f_returnEdgeLength(self.labeled_array)
        elif(name == unicode("Edge density")):
            return unicode(name), self.f_returnEdgeDensity(self.labeled_array)
        elif(name == unicode("Number of Patches")):
            return unicode(name), self.numpatches
        elif(name == unicode("Patch density")):
            return unicode(name), self.f_patchDensity(self.numpatches)
        elif(name == unicode("Greatest patch area")):
            return unicode(name), self.f_returnPatchArea(self.cl_array,self.labeled_array,self.numpatches,"max")
        elif(name == unicode("Smallest patch area")):
            return unicode(name), self.f_returnPatchArea(self.cl_array,self.labeled_array,self.numpatches,"min")
        elif(name == unicode("Mean patch area")):
            return unicode(name), self.f_returnPatchArea(self.cl_array,self.labeled_array,self.numpatches,"mean")
        elif(name == unicode("Overall Core area")):
            return unicode(name), self.f_getCoreArea(self.labeled_array)
        elif(name == unicode("Landscape division")):
            return unicode(name),     self.f_returnLandscapeDivisionIndex(self.array,self.labeled_array,self.numpatches,cl)
        elif(name == unicode("Splitting Index")):
            return unicode(name), self.f_returnSplittingIndex(self.array,self.numpatches,self.labeled_array,cl)
        elif(name == unicode("Effective Meshsize")):
            return unicode(name), self.f_returnEffectiveMeshSize(self.array,self.labeled_array,self.numpatches,cl)
        else:
            QMessageBox.warning( QDialog(), "LecoS: Warning","Unfortunately the Metric has yet to be coded.")
        
    # Connected component labeling function
    def f_ccl(self,cl_array):
        # Binary structure
        self.cl_array = cl_array
        struct = scipy.ndimage.generate_binary_structure(2,2)
        self.labeled_array, self.numpatches = ndimage.label(cl_array,struct) 
            
    ## Landscape Metrics
    # Return the total area for the given class
    def f_returnArea(self,labeled_array):
        #sizes = scipy.ndimage.sum(array, labeled_array, range(numpatches + 1)).astype(labeled_array.dtype)
        area = numpy.count_nonzero(labeled_array) * self.cellsize_2
        return area
    
    # Aggregates all class area, equals the sum of total area for each class
    def f_LandscapeArea(self):
        res = []
        for i in self.classes:
            arr = numpy.copy(self.array)
            arr[self.array!=i] = 0
            res.append(self.f_returnArea(arr))
        self.Larea = sum(res)
    
    # Return Patchdensity
    def f_patchDensity(self, numpatches):
        return (float(numpatches) / float(self.Larea))
    
    # Return array with a specific labeled patch
    def f_returnPatch(self,labeled_array,patch):
        # Make an array of zeros the same shape as `a`.
        feature = numpy.zeros_like(labeled_array, dtype=int)
        feature[labeled_array == patch] = 1
        return feature
    
    # Iter through all identified patches and count adjacent cells
    # FIXME: Obsolete. Can be deleted. Now serves as bin for snippets
    def f_IterPatches(self,array,labeled_array,numpatches,s,overlap=False):
        res = []
        if overlap:
            for i in range(1,numpatches + 1):
                feature = f_returnPatch(labeled_array,i)
                ov = (feature * ndimage.convolve((feature == 0).astype(int), s)).sum()
                res.append(ov)
        else:
            for i in range(1, numpatches + 1):
                feature = f_returnPatch(labeled_array,i)
                dil = ndimage.binary_dilation(feature,s).astype(feature.dtype)
                n = dil - feature
                res.append(numpy.count_nonzero(n))
        return sum(res)
    
        import matplotlib.pyplot as plt
        plt.imshow(feature,interpolation='nearest')
        plt.axis('on')
        plt.show()
        print a[2]
    
        s = ndimage.generate_binary_structure(2,2)
        a = numpy.zeros((6,6), dtype=numpy.int)
        a[1:5, 1:5] = 1;a[3,3] = 0
        print a
        c = ndimage.binary_dilation(a,s).astype(a.dtype)
        print c
        b = c - a
        print b
        c = ndimage.distance_transform_cdt(a == 0,metric='taxicab') == 1
        c = c.astype(int)
        plt.imshow(c,interpolation='nearest')
        plt.axis('on')
        plt.show()
        
        # correct multiple count without overlap
        b, c = ndimage.label(a,s)
        e = numpy.zeros(a.shape)
        for i in xrange(c):
            e += ndimage.distance_transform_cdt((b == i + 1) == 0) == 1
        print int(numpy.sum(e))
        # alternative
        b = ndimage.binary_closing(a,s) - a
        b = ndimage.binary_dilation(b.astype(int),s)
    
        c = ndimage.distance_transform_cdt(a == 0) == 1
    
        e = c.astype(numpy.int) * b 
    
        print numpy.sum(e)
        
        
        print ((a * ndimage.convolve((a == 1).astype(int), s)))
        print (a * ndimage.convolve((a == 0).astype(int), s)) 
        print numpy.sum(b)    
    
    # Returns total Edge length
    def f_returnEdgeLength(self,labeled_array):
        TotalEdgeLength = self.f_returnPatchPerimeter(labeled_array)
        return TotalEdgeLength * self.cellsize
    
    # Returns sum of patches perimeter
    def f_returnPatchPerimeter(self,labeled_array):
        labeled_array = self.f_setBorderZero(labeled_array) # make a border with zeroes
        TotalPerimeter = numpy.sum(labeled_array[:,1:] != labeled_array[:,:-1]) + numpy.sum(labeled_array[1:,:] != labeled_array[:-1,:])
        return TotalPerimeter
    
    # Return Edge Density
    def f_returnEdgeDensity(self,labeled_array):
        return float(self.f_returnEdgeLength(labeled_array)) / float(self.Larea)
    
    # Returns the given matrix with a zero border coloumn and row around
    def f_setBorderZero(self,matrix):
        heightFP,widthFP = matrix.shape #define hight and width of input matrix
        withBorders = numpy.ones((heightFP+(2*1),widthFP+(2*1)))*0 # set the border to borderValue
        withBorders[1:heightFP+1,1:widthFP+1]=matrix # set the interior region to the input matrix
        return withBorders
    
    # Returns the overall Core-Area
    def f_getCoreArea(self,labeled_array):
        s = ndimage.generate_binary_structure(2,2)
        newlab = ndimage.binary_erosion(labeled_array,s).astype(labeled_array.dtype)
        return ndimage.sum(newlab) * self.cellsize_2
    
    # Return greatest, smallest or mean patch area
    def f_returnPatchArea(self,cl_array,labeled_array,numpatches,what):
        sizes = ndimage.sum(cl_array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        # Iterates solutions, horribly slow
        #sizes = []
        #for i in xrange(1,numpatches+1):
        #    feature = self.f_returnPatch(labeled_array,i)
        #    area = self.f_returnArea(feature)
        #    sizes.append(area)
        if what=="max":
            return (numpy.max(sizes)*self.cellsize_2) / int(self.cl)
        elif what=="min":
            return (numpy.min(sizes)*self.cellsize_2) / int(self.cl)
        elif what=="mean":
            return (numpy.mean(sizes)*self.cellsize_2) / int(self.cl)
    
    # Returns the proportion of the labeled class in the landscape
    def f_returnProportion(self,array,cl):
        res = []
        for i in self.classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append(numpy.count_nonzero(arr))
        arr = numpy.copy(array)
        arr[array!=cl] = 0
        prop = numpy.count_nonzero(arr) / float(sum(res))
        return prop
    
    # Returns the total number of cells in the array
    def f_returnTotalCellNumber(self,array):
        return int(numpy.count_nonzero(array))
        
    # Returns a tuple with the position of the largest patch
    # FIXME: Obsolete! Maybe leave for later use
    def f_returnPosLargestPatch(self,labeled_array):
        return numpy.unravel_index(labeled_array.argmax(),labeled_array.shape)
    
    # Returns the Landscape division Index for the given array
    def f_returnLandscapeDivisionIndex(self,array,labeled_array,numpatches,cl):
        res = []
        for i in self.classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append(numpy.count_nonzero(arr))
        Lcell = float(sum(res))
        res = []
        sizes = ndimage.sum(array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        for i in sizes:
            area = (i) / int(cl)
            val = math.pow(float(area) / Lcell,2)
            res.append(val)
        return (1 - sum(res)) 
    
    # Returns the Splitting index for the given array
    def f_returnSplittingIndex(self,array,numpatches,labeled_array,cl):
        res = []
        sizes = ndimage.sum(array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        for i in sizes:
            area = (i*self.cellsize_2) / int(cl)
            val = math.pow(area,2)
            res.append(val)
        area = sum(res)
        larea2 = math.pow(self.Larea,2)
        si = float(larea2) / float(area)
        return si
    
    # Returns the Effective Mesh Size Index for the given array
    def f_returnEffectiveMeshSize(self,array,labeled_array,numpatches,cl):
        res = []
        sizes = ndimage.sum(array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        for i in sizes:
            area = (i*self.cellsize_2) / int(cl)
            res.append(math.pow(area,2))            
        Earea = sum(res)
        eM = float(Earea) / float(self.Larea)
        return eM
