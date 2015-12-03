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

# Sextante bindings
from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.core.ProcessingLog import ProcessingLog

# Import Processing bindings
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.Processing import Processing
try:
    from processing.core.ProcessingUtils import ProcessingUtils
except ImportError: # for qgis dev
    # new processing update
    from processing.tools.system import *

from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
try:
    from processing.core.QGisLayers import QGisLayers
except: # for qgis dev
    # new processing update
    from processing.tools import dataobjects, vector


# For Processing update
try:
    from processing.outputs.OutputVector import OutputVector
    from processing.outputs.OutputRaster import OutputRaster
    from processing.outputs.OutputTable import OutputTable
except ImportError:
    from processing.core.outputs import OutputVector
    from processing.core.outputs import OutputRaster
    from processing.core.outputs import OutputTable    

try:
    from processing.parameters.ParameterBoolean import ParameterBoolean
    from processing.parameters.ParameterMultipleInput import ParameterMultipleInput
    from processing.parameters.ParameterNumber import ParameterNumber
    from processing.parameters.ParameterRaster import ParameterRaster
    from processing.parameters.ParameterString import ParameterString
    from processing.parameters.ParameterTable import ParameterTable
    from processing.parameters.ParameterVector import ParameterVector
    from processing.parameters.ParameterTableField import ParameterTableField
    from processing.parameters.ParameterSelection import ParameterSelection
    from processing.parameters.ParameterRange import ParameterRange
    from processing.parameters.ParameterFixedTable import ParameterFixedTable
    from processing.parameters.ParameterExtent import ParameterExtent
    from processing.parameters.ParameterFile import ParameterFile
    from processing.parameters.ParameterCrs import ParameterCrs
except ImportError:
    from processing.core.parameters import ParameterBoolean
    from processing.core.parameters import ParameterMultipleInput
    from processing.core.parameters import ParameterNumber
    from processing.core.parameters import ParameterRaster
    from processing.core.parameters import ParameterString
    from processing.core.parameters import ParameterTable
    from processing.core.parameters import ParameterVector
    from processing.core.parameters import ParameterTableField
    from processing.core.parameters import ParameterSelection
    from processing.core.parameters import ParameterRange
    from processing.core.parameters import ParameterFixedTable
    from processing.core.parameters import ParameterExtent
    from processing.core.parameters import ParameterFile
    from processing.core.parameters import ParameterCrs

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
import lecos_functions as func

try:
    import nlmpy
except ImportError:
    nlmpy = False
     
## Algorithms ##
class SpatialRandom(GeoAlgorithm):
    # Define constants
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Spatial random"
        self.cmdName = "nlmpy:spatialrandom"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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

class PlanarGradient(GeoAlgorithm):
    # Define constants
    DIRECTION = "DIRECTION"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Planar Gradient"
        self.cmdName = "nlmpy:planargradient"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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

class EdgeGradient(GeoAlgorithm):
    # Define constants
    DIRECTION = "DIRECTION"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Edge Gradient"
        self.cmdName = "nlmpy:edgegradient"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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

class DistanceGradient(GeoAlgorithm):
    # Define constants
    SOURCE = "SOURCE"
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Distance Gradient"
        self.cmdName = "nlmpy:distancegradient"
        self.group = "Neutral landscape model (NLMpy)"

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
        
class MidpointDisplacement(GeoAlgorithm):
    
    # Define constants
    SCOR = "SCOR"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Midpoint displacement"
        self.cmdName = "nlmpy:mpd"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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
        
class RandomRectangularCluster(GeoAlgorithm):
    # Define constants
    MINL = "MINL"  
    MAXL = "MAXL"
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Random rectangular cluster"
        self.cmdName = "nlmpy:randomreccluster"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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

class RandomElementNN(GeoAlgorithm):
    # Define constants
    NELE = "NELE"    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Random element Nearest-neighbour"
        self.cmdName = "nlmpy:randomelenn"
        self.group = "Neutral landscape model (NLMpy)"

        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",True))
        self.addParameter(ParameterNumber(self.NELE, "Number of elements randomly selected", 0, None, 3))
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", True))
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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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

class RandomClusterNN(GeoAlgorithm):
    # Define constants
    NCLU = "NCLU"
    NEIG = "NEIG"
    w = ['4-neighbourhood','8-neighbourhood','diagonal']    
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Random cluster Nearest-neighbour"
        self.cmdName = "nlmpy:randomclunn"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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
        
class LinearRescale01(GeoAlgorithm):
    # Define constants
    SOURCE = "SOURCE"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Linear rescale"
        self.cmdName = "nlmpy:linearrescale"
        self.group = "Neutral landscape model (NLMpy)"

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

class RandomUniformed01(GeoAlgorithm):
    # Define constants
    MASK = "MASK"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    EXTENT = "EXTENT"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Random uniform"
        self.cmdName = "nlmpy:randomuniform"
        self.group = "Neutral landscape model (NLMpy)"

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
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")  # Processing            
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
        
        
class MeanOfCluster(GeoAlgorithm):
    # Define constants
    CLUSTERARRAY = "CLUSTERARRAY"
    SOURCE = "SOURCE"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Mean within cluster"
        self.cmdName = "nlmpy:meanofcluster"
        self.group = "Neutral landscape model (NLMpy)"

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

class ClassifyArray(GeoAlgorithm):
    # Define constants
    SOURCE = "SOURCE"
    CLASSES = "CLASSES"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    MASK = "MASK"

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Classfiy proportional Raster"
        self.cmdName = "nlmpy:classifyraster"
        self.group = "Neutral landscape model (NLMpy)"

        self.addParameter(ParameterRaster(self.SOURCE, "Cluster raster layer", True))
        self.addParameter(ParameterNumber(self.CLASSES, "Classify proportional raster to number of classes",2, None,2))

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
        cl = range(1,ncla+1)
                
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