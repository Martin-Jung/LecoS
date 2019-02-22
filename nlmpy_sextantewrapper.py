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
from qgis.core import Qgis
from qgis.core import QgsProcessingException
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum as ParameterSelection,
                       QgsProcessingParameterExtent as ParameterExtent,
                       QgsProcessingParameterNumber as ParameterNumber,
                       QgsProcessingOutputRasterLayer as OutputRaster,
                       QgsProcessingParameterRasterLayer as ParameterRaster,
                       QgsProcessingParameterRasterDestination)

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

# Import generic classes
from .lecos_sextantealgorithms import GenericProcessing
class NeutralLandscapeAlgorithm(GenericProcessing):
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def initParams(self):
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Result output"))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def getParams(self, parameters, context):
        return self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

    def group(self):
        return "Neutral landscape model (NLMpy)"
    def groupId(self):
        return "Neutral landscape model (NLMpy)"
    def helpUrl(self):
        return None
    def shortDescription(self):
        return None

#Generic parameter classes
class ExtentCSParameter(QgsProcessingAlgorithm):
    #Constant parameter names
    EXTENT = "EXTENT"
    CS = "CS"

    def initParams(self):
        self.addParameter(ParameterExtent(self.EXTENT, "Output extent",optional=False))
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", minValue=1, defaultValue=10, type=ParameterNumber.Integer))

    
    def getParams(self, parameters, context):
        ext = self.parameterAsExtent(parameters, self.EXTENT, context)
        cs = self.parameterAsInt(parameters, self.CS, context)
        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()
        gt = (xmin,cs,0,ymax,0,-cs)
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        return (gt, cols, rows)

ENUM_QGIS_NUMPY = {
    Qgis.Byte: numpy.uint8,
    Qgis.UInt16: numpy.uint16,
    Qgis.Int16: numpy.int16,
    Qgis.UInt32: numpy.uint32,
    Qgis.Int32: numpy.int32,
    Qgis.Float32: numpy.float32,
    Qgis.Float64: numpy.float64
}

class MaskParameter(QgsProcessingAlgorithm):
    MASK = "MASK"

    def initParams(self):
        self.addParameter(ParameterRaster(self.MASK, "Mask (optional)", optional=True))

    def getParams(self, parameters, context):
        mask = self.parameterAsRasterLayer(parameters, self.MASK, context)
        if mask != None:
            mask = mask.source()
            src = gdal.Open(str(mask), gdalconst.GA_ReadOnly)
            mask = src.GetRasterBand(1).ReadAsArray()      
        return mask

class SourceParameter(QgsProcessingAlgorithm):
    SOURCE = "SOURCE"

    def initParams(self):
        self.addParameter(ParameterRaster(self.SOURCE, "Data raster layer", optional=False))

    def getParams(self, parameters, context):
        inputSource = self.parameterAsRasterLayer(parameters, self.SOURCE, context).source()
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_geotrans = src.GetGeoTransform()
        cols = src.RasterXSize
        rows = src.RasterYSize
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        array = src.GetRasterBand(1).ReadAsArray()
        return (cols, rows, nodata, src_geotrans, array)

try:
    from nlmpy import nlmpy
except ImportError:
    nlmpy = False
     
## Algorithms ##
class SpatialRandom(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def displayName(self):
        return "Spatial random"
    def name(self):
        return "nlmpy:spatialrandom"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
             
        
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.random(rows, cols, mask=mask)

        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        
        

class PlanarGradient(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    DIRECTION = "DIRECTION"    
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Planar Gradient"
    def name(self):
        return "nlmpy:planargradient"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        self.addParameter(ParameterNumber(self.DIRECTION, "Direction of the gradient (optional)", minValue=0, defaultValue=0, optional=True))
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        direction = self.parameterAsInt(parameters, self.DIRECTION, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
        # Create output layer
        nodata = -9999
        
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)

        # Do the calc
        result = nlmpy.planarGradient(rows, cols,direction,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        

class EdgeGradient(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    DIRECTION = "DIRECTION"    
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Edge Gradient"
    def name(self):
        return "nlmpy:edgegradient"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        self.addParameter(ParameterNumber(self.DIRECTION, "Direction of the gradient (optional)", minValue=0,  defaultValue=0))
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        
    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        direction = self.parameterAsInt(parameters, self.DIRECTION, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.edgeGradient(rows, cols,direction,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        

class DistanceGradient(NeutralLandscapeAlgorithm, MaskParameter, SourceParameter):
    # Define constants
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Distance Gradient"
    def name(self):
        return "nlmpy:distancegradient"

    def initAlgorithm(self, config):
        SourceParameter.initParams(self)
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", minValue=10,  defaultValue=1))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        inputSource = self.parameterAsRasterLayer(parameters, self.SOURCE, context).source()
        mask = MaskParameter.getParams(self, parameters, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        cs = self.parameterAsInt(parameters, self.CS, context)
        
        # Source 
        cols, rows, nodata, src_geotrans, array = SourceParameter.getParams(self, parameters, context)        
        # Do the calc
        result = nlmpy.distanceGradient(array,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        return {self.OUTPUT_RASTER: output}
        
        
class MidpointDisplacement(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    SCOR = "SCOR"    
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Midpoint displacement"
    def name(self):
        return "nlmpy:mpd"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        self.addParameter(ParameterNumber(self.SCOR, "Level of Spatial Autocorrelation (0 - 1)", minValue=0, maxValue=1, defaultValue=0.5, type=ParameterNumber.Double))
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        
    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        scor = self.parameterAsDouble(parameters, self.SCOR, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
        
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.mpd(rows, cols, scor, mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        
        
class RandomRectangularCluster(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    MINL = "MINL"  
    MAXL = "MAXL"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random rectangular cluster"
    def name(self):
        return "nlmpy:randomreccluster"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        self.addParameter(ParameterNumber(self.MINL, "Minimum length of each cluster)", minValue=0,  defaultValue=1))
        self.addParameter(ParameterNumber(self.MAXL, "Maximum length of each cluster", minValue=0,  defaultValue=10))        
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        minl = self.parameterAsInt(parameters, self.MINL, context)
        maxl = self.parameterAsInt(parameters, self.MAXL, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
             
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.randomRectangularCluster(rows, cols,minl,maxl,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        

class RandomElementNN(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    NELE = "NELE"    
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")

    def displayName(self):
        return "Random element Nearest-neighbour"
    def name(self):
        return "nlmpy:randomelenn"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        self.addParameter(ParameterNumber(self.NELE, "Number of elements randomly selected", minValue=0, defaultValue=3, type=ParameterNumber.Integer))
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        nele = self.parameterAsInt(parameters, self.NELE, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.randomElementNN(rows, cols,nele,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}


class RandomClusterNN(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    NCLU = "NCLU"
    NEIG = "NEIG"
    w = ['4-neighbourhood','8-neighbourhood','diagonal']    
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random cluster Nearest-neighbour"
    def name(self):
        return "nlmpy:randomclunn"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        self.addParameter(ParameterNumber(self.NCLU, "Proportions of elements to form cluster ( 0 - 1 )", minValue=0, maxValue=1, defaultValue=0.5, type=ParameterNumber.Double))
        self.addParameter(ParameterSelection(self.NEIG, "Neighbourhood structure", self.w, 0))
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        nclu = self.parameterAsDouble(parameters, self.NCLU, context)
        what = self.w[self.parameterAsEnum(parameters, self.NEIG, context)]        
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
        
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.randomClusterNN(rows, cols,nclu,what,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        
        
class LinearRescale01(NeutralLandscapeAlgorithm, SourceParameter):
    # Define constants
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Linear rescale"
    def name(self):
        return "nlmpy:linearrescale"

    def initAlgorithm(self, config):
        SourceParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", minValue=10,  defaultValue=1))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        inputSource = self.parameterAsRasterLayer(parameters, self.SOURCE, context).source()
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        cs = self.parameterAsInt(parameters, self.CS, context)
        
        # Source 
        cols, rows, nodata, src_geotrans, array = SourceParameter.getParams(self, parameters, context)        
        # Do the calc
        result = nlmpy.linearRescale01(array)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        return {self.OUTPUT_RASTER: output}
        

class RandomUniformed01(NeutralLandscapeAlgorithm, ExtentCSParameter, MaskParameter):
    # Define constants
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Random uniform"
    def name(self):
        return "nlmpy:randomuniform"

    def initAlgorithm(self, config):
        ExtentCSParameter.initParams(self)
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        mask = MaskParameter.getParams(self, parameters, context)
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        
        # Create output layer
        nodata = -9999
        gt, cols, rows = ExtentCSParameter.getParams(self, parameters, context)
        
        # Do the calc
        result = nlmpy.randomUniform01(rows, cols, mask=mask)

        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,gt)
        return {self.OUTPUT_RASTER: output}
        
        
        
class MeanOfCluster(NeutralLandscapeAlgorithm, SourceParameter):
    # Define constants
    CLUSTERARRAY = "CLUSTERARRAY"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"
    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Mean within cluster"
    def name(self):
        return "nlmpy:meanofcluster"

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.CLUSTERARRAY, "Clustered raster layer", optional=False))
        SourceParameter.initParams(self)
        
        NeutralLandscapeAlgorithm.initParams(self)
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", minValue=10,  defaultValue=1))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        clusterSource = self.parameterAsRasterLayer(parameters, self.CLUSTERARRAY, context)        .source()
        inputSource = self.parameterAsRasterLayer(parameters, self.SOURCE, context).source()
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        cs = self.parameterAsInt(parameters, self.CS, context)
        
        # Cluster array
        src = gdal.Open(str(clusterSource), gdalconst.GA_ReadOnly)
        cl_array = src.GetRasterBand(1).ReadAsArray()  
        
        # Source 
        cols, rows, nodata, src_geotrans, array = SourceParameter.getParams(self, parameters, context)                
        # Do the calc
        result = nlmpy.meanOfCluster(cl_array,array)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        return {self.OUTPUT_RASTER: output}
        

class ClassifyArray(NeutralLandscapeAlgorithm, MaskParameter, SourceParameter):
    # Define constants
    CLASSES = "CLASSES"
    # Output
    OUTPUT_RASTER = "OUTPUT_RASTER"
    CS = "CS"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_nlmpy.png")


    def displayName(self):
        return "Classify proportional Raster"
    def name(self):
        return "nlmpy:classifyraster"

    def initAlgorithm(self, config):
        self.addParameter(ParameterRaster(self.SOURCE, "Cluster raster layer", optional=False))
        self.addParameter(ParameterNumber(self.CLASSES, "Classify proportional raster to number of classes", minValue=2,  defaultValue=2))
        MaskParameter.initParams(self)
        NeutralLandscapeAlgorithm.initParams(self)
        self.addParameter(ParameterNumber(self.CS, "Output Cellsize", minValue=10,  defaultValue=1))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        ncla = self.parameterAsInt(parameters, self.CLASSES, context)        
        inputSource = self.parameterAsRasterLayer(parameters, self.SOURCE, context).source()
        output = NeutralLandscapeAlgorithm.getParams(self, parameters, context)
        cs = self.parameterAsInt(parameters, self.CS, context)
        
        mask = MaskParameter.getParams(self, parameters, context)
        
        # Source 
        cols, rows, nodata, src_geotrans, array = SourceParameter.getParams(self, parameters, context)        
        # Classes
        cl = list(range(1,ncla+1))
                
        # Do the calc
        result = nlmpy.classifyArray(array,cl,mask)
                    
        # Create output raster
        func.createRaster(output,cols,rows,result,nodata,src_geotrans)
        return {self.OUTPUT_RASTER: output}
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None