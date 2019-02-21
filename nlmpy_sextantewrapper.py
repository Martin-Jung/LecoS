# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LecoS
                                 A QGIS plugin
 Contains analytical functions for landscape analysis
                              -------------------
        begin                : 2012-09-06
        copyright            : (C) 2013 by Martin Jung
        email                : martinjung at zoho.com
 ***************************************************************************/

/***************************************************************************
from qgis.PyQt.QtCore import *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
# Import PyQT bindings
from builtins import str
from builtins import range
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *


# Import Processing bindings
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import (QgsProcessingParameterEnum as ParameterSelection,
                       QgsProcessingParameterExtent as ParameterExtent,
                       QgsProcessingParameterNumber as ParameterNumber,
                       QgsProcessingOutputRasterLayer as OutputRaster,
                       QgsProcessingParameterRasterLayer as ParameterRaster)

# Import numpy and scipy
import numpy
try:
    import scipy
except ImportError:
    QMessageBox.critical(QDialog(),"LecoS: Warning","Please install scipy (http://scipy.org/) in your QGIS python path.")
    sys.exit(0)
from scipy import ndimage # import ndimage module seperately for easy access

# Import GDAL and ogr
try:
    from osgeo import gdal
except ImportError:
    import gdal
try:
    from osgeo import gdalconst
except ImportError:
    import gdalconst
try:
    from osgeo import ogr
except ImportError:
    import ogr
try:
    import string
except ImportError:
    pass
# Register gdal and ogr drivers
#if hasattr(gdal,"AllRegister"): # Can register drivers
#    gdal.AllRegister() # register all gdal drivers
#if hasattr(ogr,"RegisterAll"):
#    ogr.RegisterAll() # register all ogr drivers

import os, sys

# Import functions and metrics
from . import lecos_functions as func

try:
    import nlmpy
except ImportError:
    nlmpy = False
     
## Algorithms ##
class SpatialRandom(QgsProcessingAlgorithm):
    # Define constants
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Spatial random"
    def name(self):
        return "nlmpy:spatialrandom"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)        
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.random(rows, cols, mask=mask)

        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class PlanarGradient(QgsProcessingAlgorithm):
    # Define constants
    DIRECTION = "DIRECTION"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Planar Gradient"
    def name(self):
        return "nlmpy:planargradient"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterNumber(self.DIRECTION, "Direction of the gradient (optional)", 0, None, 0))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)
        direction = self.getParameterValue(self.DIRECTION)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.planarGradient(rows, cols,direction,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class EdgeGradient(QgsProcessingAlgorithm):
    # Define constants
    DIRECTION = "DIRECTION"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Edge Gradient"
    def name(self):
        return "nlmpy:edgegradient"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterNumber(self.DIRECTION, "Direction of the gradient (optional)", 0, None, 0))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)
        direction = self.getParameterValue(self.DIRECTION)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.edgeGradient(rows, cols,direction,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class DistanceGradient(QgsProcessingAlgorithm):
    # Define constants
    SOURCE = "SOURCE"
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Distance Gradient"
    def name(self):
        return "nlmpy:distancegradient"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.SOURCE, "Source raster layer", True))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        inputSource = self.getParameterValue(self.SOURCE)
        mask = self.getParameterValue(self.MASK)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        
        # Source 
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_geotrans = src.GetGeoTransform()
        cols = src.RasterXSize
        rows = src.RasterYSize
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        array = src.GetRasterBand(1).ReadAsArray()  
        
        # Do the calc
        result = nlmpy.distanceGradient(array,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None
        
class MidpointDisplacement(QgsProcessingAlgorithm):
    
    # Define constants
    SCOR = "SCOR"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Midpoint displacement"
    def name(self):
        return "nlmpy:mpd"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True)) 
        self.addParameter(ParameterNumber(self.SCOR, "Level of Spatial Autocorrelation (0 - 1)", False,  True,0.5))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)
        scor = self.getParameterValue(self.SCOR)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.mpd(rows, cols,scor,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None
        
class RandomRectangularCluster(QgsProcessingAlgorithm):
    # Define constants
    MINL = "MINL"  
    MAXL = "MAXL"
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random rectangular cluster"
    def name(self):
        return "nlmpy:randomreccluster"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterNumber(self.MINL, "Minimum length of each cluster)", 0, None, 1))
        self.addParameter(ParameterNumber(self.MAXL, "Maximum length of each cluster", 0, None, 10))        
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)
        minl = self.getParameterValue(self.MINL)
        maxl = self.getParameterValue(self.MAXL)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.randomRectangularCluster(rows, cols,minl,maxl,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class RandomElementNN(QgsProcessingAlgorithm):
    # Define constants
    NELE = "NELE"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def createInstance(self):
        return RandomElementNN()
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random element Nearest-neighbour"
    def name(self):
        return "nlmpy:randomelenn"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent", optional=True))
        self.addParameter(ParameterNumber(self.NELE, "Number of elements randomly selected", 0, None, 3))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", optional=True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)
        nele = self.getParameterValue(self.NELE)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.randomElementNN(rows, cols,nele,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class RandomClusterNN(QgsProcessingAlgorithm):
    # Define constants
    NCLU = "NCLU"
    NEIG = "NEIG"
    w = ['4-neighbourhood','8-neighbourhood','diagonal']    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random cluster Nearest-neighbour"
    def name(self):
        return "nlmpy:randomclunn"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterNumber(self.NCLU, "Proportions of elements to form cluster ( 0 - 1 )",False, True,0.5))
        self.addParameter(ParameterSelection(self.NEIG, "Neighbourhood structure", self.w, 0))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)
        nclu = self.getParameterValue(self.NCLU)
        what = self.w[self.getParameterValue(self.NEIG)]        
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.randomClusterNN(rows, cols,nclu,what,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None      
        
class LinearRescale01(QgsProcessingAlgorithm):
    # Define constants
    SOURCE = "SOURCE"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Linear rescale"
    def name(self):
        return "nlmpy:linearrescale"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.SOURCE, "Source raster layer", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        inputSource = self.getParameterValue(self.SOURCE)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        
        # Source 
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_geotrans = src.GetGeoTransform()
        cols = src.RasterXSize
        rows = src.RasterYSize
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        array = src.GetRasterBand(1).ReadAsArray()  
        
        # Do the calc
        result = nlmpy.linearRescale01(array)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None      

class RandomUniformed01(QgsProcessingAlgorithm):
    # Define constants
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random uniform"
    def name(self):
        return "nlmpy:randomuniform"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        mask = self.getParameterValue(self.MASK)        
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        ext = self.getParameterValue(self.EXTENT)
        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()           
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise QgsProcessingException("Please set an extent for the generated raster")  # Processing            
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Do the calc
        result = nlmpy.randomUniform01(rows, cols, mask=mask)

        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None              
        
        
class MeanOfCluster(QgsProcessingAlgorithm):
    # Define constants
    CLUSTERARRAY = "CLUSTERARRAY"
    SOURCE = "SOURCE"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Mean within cluster"
    def name(self):
        return "nlmpy:meanofcluster"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.CLUSTERARRAY, "Clustered raster layer", True))
        self.addParameter(ParameterRaster(self.SOURCE, "Data raster layer", True))
        
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        clusterSource = self.getParameterValue(self.CLUSTERARRAY)        
        inputSource = self.getParameterValue(self.SOURCE)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        
        # Cluster array
        src = gdal.Open(str(clusterSource), gdalconst.GA_ReadOnly)
        cl_array = src.GetRasterBand(1).ReadAsArray()  
        
        # Source 
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_geotrans = src.GetGeoTransform()
        cols = src.RasterXSize
        rows = src.RasterYSize
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        array = src.GetRasterBand(1).ReadAsArray()  
                
        # Do the calc
        result = nlmpy.meanOfCluster(cl_array,array)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None            

class ClassifyArray(QgsProcessingAlgorithm):
    # Define constants
    SOURCE = "SOURCE"
    CLASSES = "CLASSES"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    MASK = "MASK"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Classfiy proportional Raster"
    def name(self):
        return "nlmpy:classifyraster"
    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.SOURCE, "Cluster raster layer", True))
        self.addParameter(ParameterNumber(self.CLASSES, "Classify proportional raster to number of classes",2, None,2))

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))        
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", 10, None, 1))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        ncla = self.getParameterValue(self.CLASSES)        
        inputSource = self.getParameterValue(self.SOURCE)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        cs = self.getParameterValue(self.CS)
        
        mask = self.getParameterValue(self.MASK)        
        if mask != None:
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()      
        
        # Source 
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_geotrans = src.GetGeoTransform()
        cols = src.RasterXSize
        rows = src.RasterYSize
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        array = src.GetRasterBand(1).ReadAsArray()  
        
        # Classes
        cl = list(range(1,ncla+1))
                
        # Do the calc
        result = nlmpy.classifyArray(array,cl,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None