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
import operator
from osgeo import gdal, gdalnumeric, ogr, osr
import Image, ImageDraw
from scipy import ndimage
try:
    gdal.AllRegister() # register all gdal drivers
except AttributeError:
    QMessageBox.warning(QDialog(),"LecoS: Warning","The gdal driver register command failed. LecoS might still work, but there is a chance of non working gdal file support.")

gdal.UseExceptions()
ogr.UseExceptions()

# Many functions stolen from here :-)
# http://geospatialpython.com/2011/02/clip-raster-using-shapefile.html 
class BatchConverter():
    def __init__(self,rasterPath,vectorPath):
        
        # load as a gdal image to get geotransform and full array
        self.srcImage = gdal.Open(str(rasterPath))
        self.geoTrans = self.srcImage.GetGeoTransform()
        try:
            self.srcArray = self.srcImage.GetRasterBand(1).ReadAsArray() # Convert first band to array
        except ValueError:
            QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
            return

        # Create an OGR layer from a boundary shapefile used to clip
        self.shapef = ogr.Open("%s" % str(vectorPath))
        self.lyr = self.shapef.GetLayer()
        
    #Iterate through all features and executes the named command
    #Values are returned as array per feature
    def go(self,cmd,cl):
        res = []
        for i in xrange(0,self.lyr.GetFeatureCount()):
            if self.lyr.GetFeatureCount() == 1:
                poly = self.lyr.GetFeature(0)
            else:
                poly = self.lyr.GetNextFeature()
            array = self.getClipArray(poly)
            # Unclassified Methods
            if(cmd == "sum"):
                r = self.returnArraySum(array)
            elif(cmd == "mean"):
                r = self.returnArrayMean(array)
            elif(cmd == "std"):
                r = self.returnArrayStd(array)
            elif(cmd == "med"):
                r = self.returnArrayMedi(array)
            elif(cmd == "max"):
                r = self.returnArrayMax(array)
            elif(cmd == "min"):
                r = self.returnArrayMin(array)
            elif(cmd == "lowq"):
                r = self.returnArrayLowerQuant(array)
            elif(cmd == "uppq"):
                r = self.returnArrayHigherQuant(array)
            # Classified Methods
            elif(cmd == "LCnum"):
                r = self.returnLCnumber(array,cl)
            elif(cmd == "LCprop"):
                r = self.returnLCproportion(array,cl)
            else:
                QMessageBox.warning(QDialog(),"LecoS: Error","The function couldn't be found")
            b = [poly.GetFID(),r]
            res.append(b)
        return res
    
    
    # This function will convert the rasterized clipper shapefile 
    # to a mask for use within GDAL.    
    def imageToArray(self,i):
        """
        Converts a Python Imaging Library array to a 
        gdalnumeric image.
        """
        try:
            a=gdalnumeric.fromstring(i.tostring(),'b')
        except SystemError:
            QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
            return

        a.shape=i.im.size[1], i.im.size[0]
        return a

    def arrayToImage(self,a):
        """
        Converts a gdalnumeric array to a 
        Python Imaging Library Image.
        """
        i=Image.fromstring('L',(a.shape[1],a.shape[0]),
                (a.astype('b')).tostring())
        return i
    
    def world2Pixel(self,geoMatrix, x, y):
        """
        Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
        the pixel location of a geospatial coordinate 
        """
        ulX = geoMatrix[0]
        ulY = geoMatrix[3]
        xDist = geoMatrix[1]
        yDist = geoMatrix[5]
        rtnX = geoMatrix[2]
        rtnY = geoMatrix[4]
        pixel = int((x - ulX) / xDist)
        line = int((ulY - y) / xDist)
        return (pixel, line) 
    
    # Returns an array from the given polygon feature
    def getClipArray(self,poly):
        # Convert the layer extent to image pixel coordinates
        minX, maxX, minY, maxY = self.lyr.GetExtent()
        ulX, ulY = self.world2Pixel(self.geoTrans, minX, maxY)
        lrX, lrY = self.world2Pixel(self.geoTrans, maxX, minY)

        # Calculate the pixel size of the new image
        pxWidth = int(lrX - ulX)
        pxHeight = int(lrY - ulY)
        
        # Clip the raster to the shapes boundingbox
        clip = self.srcArray[ulY:lrY, ulX:lrX]

        # Create a new geomatrix for the image
        geoTrans = list(self.geoTrans)
        geoTrans[0] = minX
        geoTrans[3] = maxY
        
        # Map points to pixels for drawing the 
        # boundary on a blank 8-bit, 
        # black and white, mask image.
        points = []
        pixels = []
        geom = poly.GetGeometryRef()
        pts = geom.GetGeometryRef(0)
        for p in range(pts.GetPointCount()):
            points.append((pts.GetX(p), pts.GetY(p)))
        for p in points:
            pixels.append(self.world2Pixel(geoTrans, p[0], p[1]))
        rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
        rasterize = ImageDraw.Draw(rasterPoly)
        rasterize.polygon(pixels, 0)
        mask = self.imageToArray(rasterPoly)   

        # Clip the image using the mask
        clip2 = gdalnumeric.choose(mask,(clip, 0)).astype(self.srcArray.dtype)
        return clip2
    
    # Returns number of given cells
    def returnLCnumber(self,array,cl):
        return int(numpy.count_nonzero(array[array==cl]))
    
    # Returns the proportion of the labeled class in the landscape
    def returnLCproportion(self,array,cl):
        res = []
        classes = sorted(numpy.unique(array)) # get classes
        # Value 0 seems to be the default nodata-value
        for i in classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append(numpy.count_nonzero(arr))
        arr = numpy.copy(array)
        arr[array!=cl] = 0
        prop = numpy.count_nonzero(arr) / float(sum(res))
        return prop

    ## Unclassified Methods ##
    # Returns sum of clipped raster cells
    def returnArraySum(self,array):
        return numpy.sum(array)
    
    # Returns mean of clipped raster cells
    def returnArrayMean(self,array):
        return numpy.mean(array[array!=0])
        
    # Returns standard deviation of clipped raster cells
    def returnArrayStd(self,array):
        return numpy.std(array[array!=0])
    
    # Returns the minimum of clipped raster cells
    def returnArrayMin(self,array):
        return numpy.min(array[array!=0])
    
    # Returns the minimum of clipped raster cells
    def returnArrayMax(self,array):
        return numpy.max(array[array!=0])
        
    # Returns the median of clipped raster cells
    def returnArrayMedi(self,array):
        return numpy.median(array[array!=0])
    
    # Returns the weighed average of clipped raster cells
    def returnArrayLowerQuant(self,array):
        return scipy.percentile(array[array!=0],25)
    
    # Returns the weighed average of clipped raster cells
    def returnArrayHigherQuant(self,array):
        return scipy.percentile(array[array!=0],75)
    