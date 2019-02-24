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
from __future__ import absolute_import
# Import Processing bindings
from builtins import str
from builtins import range
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterBoolean as ParameterBoolean,
                       QgsProcessingParameterEnum as ParameterSelection,
                       QgsProcessingParameterExtent as ParameterExtent,
                       QgsProcessingParameterNumber as ParameterNumber,
                       QgsProcessingOutputRasterLayer as OutputRaster,
                       QgsProcessingParameterRasterLayer as ParameterRaster,
                       QgsProcessingParameterVectorLayer as ParameterVector,
                       QgsProcessingParameterMatrix as ParameterTable,
                       QgsProcessingOutputVectorLayer as OutputTable,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField as ParameterTableField)


from qgis.core import QgsProcessingException

# For Processing update
# Import PyQT bindings
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *
# QGIS utils
import qgis.utils

# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect
from os import path

# Import functions and metrics
from . import lecos_functions as func

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

# Register gdal and ogr drivers
#if hasattr(gdal,"AllRegister"): # Can register drivers
#    gdal.AllRegister() # register all gdal drivers
#if hasattr(ogr,"RegisterAll"):
#    ogr.RegisterAll() # register all ogr drivers

TYPES_PYTHON_QVARIANT = { 
    int: QVariant.Int,
    float: QVariant.Double
}

# Generic class containing commom methods for all algorithms
class GenericProcessing(QgsProcessingAlgorithm):
    def createInstance(self):
        return self.__class__()

    def helpPath(self):
        htmlPath = os.path.join(os.path.dirname(__file__), "sextante_info", self.name() + ".html")
        if os.path.isfile(htmlPath):
            return htmlPath
        else:
            return ""

    def shortDescription(self):
        helpPath = self.helpPath()
        if (helpPath):
            helpFile = open(helpPath, 'r')
            htmlString = helpFile.read()
            helpString = htmlString.split('<p>')[2].replace('</p>\n\n','')
            return helpString
        return None

    def helpUrl(self):
        helppath = self.helpPath()
        if (helppath):
            return helppath
        else:
            return None


# Classes for grouping algorithms
class LandscapePreparationAlgorithm(GenericProcessing):
    def group(self):
        return "Landscape preparation"
    def groupId(self):
        return 'Landscape preparation'

class LandscapeModificationAlgorithm(GenericProcessing):
    def group(self):
        return "Landscape modifications"
    def groupId(self):
        return "Landscape modifications"

class LandscapeStatisticsAlgorithm(GenericProcessing):
    def group(self):
        return "Landscape statistics"
    def groupId(self):
        return "Landscape statistics"

class LandscapeVectorOverlayAlgorithm(GenericProcessing):
    def group(self):
        return "Landscape vector overlay"
    def groupId(self):
        return "Landscape vector overlay"
    

## Landscape preperation
# Creates a random landscape from a given distribution
class CreateRandomLandscape(LandscapePreparationAlgorithm):
    # Define constants
    WHAT = "WHAT"
    w = ['Constant value','Random integer','Uniform','Normal','Exponential','Poisson','Gamma','Binomial','Geometric','Negative binomial','lognormal','Weibull']
    EXTENT = "EXTENT"
    CELL_SIZE = "CELL_SIZE"
    MIN = "MIN"
    MAX = "MAX"
    MEAN = "MEAN"
    STD = "STD"
    OUTPUT_FILE = "OUTPUT_FILE"
    
    def __init__(self):
        super().__init__()
        self.controller = None

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_randomdistribution.png")
       
    def displayName(self):
        return "Create random Landscape (Distribution)"

    def name(self):
        return "createrandomraster"
 
    def initAlgorithm(self, config):
        self.addParameter(ParameterSelection(self.WHAT, "Choose value distribution", self.w, 0))
        self.addParameter(ParameterExtent(self.EXTENT, "New extent"))
        self.addParameter(ParameterNumber(self.MIN, "Minimum / Alpha", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(ParameterNumber(self.MAX, "Maximum / Beta", type=ParameterNumber.Integer, defaultValue=10))
        self.addParameter(ParameterNumber(self.MEAN, "Mean / Number", type=ParameterNumber.Integer, defaultValue=5))
        self.addParameter(ParameterNumber(self.STD, "Standard Deviation / Probability", type=ParameterNumber.Integer, defaultValue=2))
        self.addParameter(ParameterNumber(self.CELL_SIZE, "New cell size", type=ParameterNumber.Integer, defaultValue=25)) 
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_FILE, "Result output"))   
        self.addOutput(OutputRaster(self.OUTPUT_FILE, "Result output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        # Retrieve the values of the parameters entered by the user
        what = self.w[self.parameterAsEnum(parameters, self.WHAT, context)]
        ext = self.parameterAsExtent(parameters, self.EXTENT, context)
        mini = self.parameterAsInt(parameters, self.MIN, context)
        maxi = self.parameterAsInt(parameters, self.MAX, context)
        avg = self.parameterAsInt(parameters, self.MEAN, context)
        std = self.parameterAsInt(parameters, self.STD, context)
        cs  =  self.parameterAsInt(parameters, self.CELL_SIZE, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_FILE, context)
        # Create output layer
        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()
        gt = (xmin,cs,0,ymax,0,-cs)
        nodata = -9999
        cols = int( round( (xmax-xmin)/cs ) )
        rows = int( round( (ymax-ymin)/cs ) )
        
        # Processing
        if what == 'Constant value':
            # Create a raster with the given constant number
            array = numpy.ones((rows,cols))
            array[array==1] = float( avg )       
        elif what == 'Random integer':
            # xmin, xmax, ymin, ymax
            array = numpy.random.random_integers(float(mini),float(maxi),(rows,cols))        
        elif what == 'Uniform':
            array = numpy.random.uniform(mini,maxi,(rows,cols))
        elif what == "Normal":
            array = numpy.random.normal(avg,std,(rows,cols))
        elif what == "Exponential":
            array = numpy.random.exponential(avg,(rows,cols))
        elif what == "Poisson":
            array = numpy.random.poisson(avg,(rows,cols))
        elif what == "Gamma":
            array = numpy.random.gamma(mini,maxi,(rows,cols))
        elif what == "Binomial":
            try:
                array = numpy.random.binomial(avg,std,(rows,cols))
            except ValueError:
                raise QgsProcessingException("The Probability can not be greater than 1")
        elif what == "Geometric":
            try:            
                array = numpy.random.geometric(std,(rows,cols))
            except ValueError:
                raise QgsProcessingException("The Probability can not be greater than 1")
        elif what == "Negative binomial":
            try:
                array = numpy.random.negative_binomial(avg,std,(rows,cols))
            except ValueError:
                raise QgsProcessingException("The Probability can not be greater than 1")                
        elif what == "lognormal":
            array = numpy.random.lognormal(avg,std,(rows,cols))
        elif what == "Weibull":
            array = numpy.random.weibull(avg,(rows,cols))
                
        # Create output raster
        func.createRaster(output,cols,rows,array,nodata,gt)
        return {self.OUTPUT_FILE: output}

    
# Inspired from here: http://stackoverflow.com/questions/10454316/how-to-project-and-resample-a-grid-to-match-another-grid-with-gdal-python
class MatchLandscapes(LandscapePreparationAlgorithm):
    # Define constants
    LAND1 = "LAND1"
    LAND2 = "LAND2"
    INTERP = "INTERP"
    i = ['Bilinear','Cubic','Cubicspline','Lanczos','NearestNeighbour']
    OUTPUT_RASTER = "OUTPUT_RASTER"
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_matchlandscapes.png")
    def displayName(self):
        return "Match two landscapes"
    def name(self):
        return "preplandscape"

    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND1, "Source landscape", optional=False))
        self.addParameter(ParameterRaster(self.LAND2, "Target landscape", optional=False))
        self.addParameter(ParameterSelection(self.INTERP, "Interpolation mode", self.i, 0))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Result output"))   
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        # Retrieve the values of the parameters entered by the user
        inputSource = self.parameterAsRasterLayer(parameters, self.LAND1, context).source()
        inputTarget = self.parameterAsRasterLayer(parameters, self.LAND2, context).source()
        interp = self.i[self.parameterAsEnum(parameters, self.INTERP, context)]
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
                
        # Processing
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_proj = src.GetProjection()
        src_geotrans = src.GetGeoTransform()
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        
        # We want a section of source that matches this:
        match_ds = gdal.Open(str(inputTarget), gdalconst.GA_ReadOnly)
        match_proj = match_ds.GetProjection()
        match_geotrans = match_ds.GetGeoTransform()
        wide = match_ds.RasterXSize
        high = match_ds.RasterYSize
        
        # Output / destination
        try:
            # try create File driver based in path
            dst = gdal.GetDriverByName('GTiff').Create(output, wide, high, 1, gdalconst.GDT_Float32)
        except RuntimeError:
            raise QgsProcessingException("Could not generate output file")
            
        dst.SetGeoTransform( match_geotrans )
        dst.SetProjection( match_proj)
        dst.GetRasterBand(1).SetNoDataValue(nodata) # write old nodata value

        # Do the work
        if interp == 'Bilinear':
            gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_Bilinear)
        elif interp == 'Cubic':
            gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_Cubic)        
        elif interp == 'Cubicspline':
            gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_CubicSpline)            
        elif interp == 'Lanczos':
            gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_Lanczos)            
        elif interp == 'NearestNeighbour':
            gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_NearestNeighbour)
                    
        del dst # Flush
        return {self.OUTPUT_RASTER: output}
        

class RasterWithRasterClip(LandscapePreparationAlgorithm):
    # Define constants
    LAND1 = "LAND1"
    LAND2 = "LAND2"
    OUTPUT_RASTER = "OUTPUT_RASTER"
    

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_clipRaster.png")

    def displayName(self):
        return "Intersect Landscapes"
    def name(self):
        return "landintersect"

    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND1, "Source landscape", optional=False))
        self.addParameter(ParameterRaster(self.LAND2, "Target landscape", optional=False))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Result output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputSource = self.parameterAsRasterLayer(parameters, self.LAND1, context)
        inputTarget = self.parameterAsRasterLayer(parameters, self.LAND2, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
        

        if inputSource.crs() != inputTarget.crs():
            raise QgsProcessingException("Make sure both raster layer have the same projection")
                    
        # Processing
        src = gdal.Open(str(inputSource.source()), gdalconst.GA_ReadOnly)
        src_proj = src.GetProjection()
        src_geotrans = src.GetGeoTransform()
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        wide = src.RasterXSize
        high = src.RasterYSize
        
        # r1 has left, top, right, bottom of dataset's bounds in geospatial coordinates.
        r1 = [src_geotrans[0], src_geotrans[3], src_geotrans[0] + (src_geotrans[1] * wide), src_geotrans[3] + (src_geotrans[5] * high)]

        # We want a section of source that matches this:
        match_ds = gdal.Open(str(inputTarget.source()), gdalconst.GA_ReadOnly)
        match_proj = match_ds.GetProjection()
        match_geotrans = match_ds.GetGeoTransform()
        wide = match_ds.RasterXSize
        high = match_ds.RasterYSize
        
        # the same as above but for the match
        r2 = [match_geotrans[0], match_geotrans[3], match_geotrans[0] + (match_geotrans[1] * wide), match_geotrans[3] + (match_geotrans[5] * high)]

        #Intersection:
        intersection = [max(r1[0], r2[0]), min(r1[1], r2[1]), min(r1[2], r2[2]), max(r1[3], r2[3])]
        
        # Test if they are intersecting
        if (intersection[2] < intersection[0]) or (intersection[1] < intersection[3]):
            raise QgsProcessingException("Landscape layers are not intersecting.")

        else:
            # Convert to pixels
            p1 = self.world2Pixel(src_geotrans,intersection[0],intersection[1])
            p2 = self.world2Pixel(src_geotrans,intersection[2],intersection[3])
            band = src.GetRasterBand(1)            
            result = band.ReadAsArray(p1[0], p1[1], p2[0] - p1[0], p2[1] - p1[1], p2[0] - p1[0], p2[1] - p1[1])
            
            # Write to new raster
            func.exportRaster(result,inputTarget.source(),output,nodata)
            return {self.OUTPUT_RASTER: output}


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


## Landscape Statistics
from . import landscape_statistics as lcs
class LandscapeStatistics(LandscapeStatisticsAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    METRIC = "METRIC"
    METRICsel = ["Mean", "Sum","Minimum","Maximum","Standard deviation","Lower quantile","Median","Upper quantile","Shannon Diversity Index","Eveness","Simpson Diversity Index"]
    m = ["LC_Mean","LC_Sum","LC_Min","LC_Max","LC_SD","LC_LQua","LC_Med","LC_UQua","DIV_SH","DIV_EV","DIV_SI"]
    OUTPUT_FILE = "OUTPUT_FILE"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

    def displayName(self):
        return "Landscape wide statistics"
    def name(self):
        return "landscapestat"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterSelection(self.METRIC, "What to calculate", self.METRICsel, 0))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        rasterlayer = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context)
        inputFilename = rasterlayer.source()
        what = self.m[self.parameterAsEnum(parameters, self.METRIC, context)]

        # Processing
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))
        
        if Qgis.QGIS_VERSION_INT < 10900:
            pixelSize = rasterlayer.rasterUnitsPerPixel()
        else:
            pixelSize = rasterlayer.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = rasterlayer.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                raise QgsProcessingException("The cells in the landscape layer are not square. Calculated values will be incorrect")
        
        cl_analys = lcs.LandCoverAnalysis(array,pixelSize,classes)
        res = []
        name, result = cl_analys.execLandMetric(what,nodata)                                    
        res.append([name, float(result.item())])
        # Create the output
        output = func.getSinkWithValues(self, 
                                        parameters, 
                                        self.OUTPUT_FILE, 
                                        context, 
                                        values = res, 
                                        titles = ["Metric","Value"],
                                        types = [QVariant.String, QVariant.Double])
        return {self.OUTPUT_FILE: output}


# Lists all unique raster cells of a raster
# Returns the total number per cell in a table
class CountRasterCells(LandscapeStatisticsAlgorithm):
    # Define constants
    RASTER = "RASTER"
    BAND = "BAND"
    OUTPUT_FILE = "OUTPUT_FILE"
     

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_countRastercells.png")
    def displayName(self):
        return "Count Raster Cells"
    def name(self):
        return "countrastercell"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.RASTER, "Raster layer", optional=False))
        self.addParameter(ParameterNumber(self.BAND, "Which Raster band (1 default)", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Result output", type=QgsProcessing.TypeVector))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Result output", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.RASTER, context).source()
        band = self.parameterAsInt(parameters, self.BAND, context)

        # Use GDAL to open the raster
        raster = gdal.Open(str(inputFilename))
        band = raster.GetRasterBand(band)
        try:
            array =  band.ReadAsArray() 
        except ValueError:
            raise QgsProcessingException("Input Raster to big. Try to slice it up.")
        nodata = band.GetNoDataValue() # Get Nodata-value
        raster = None # close gdal

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))
                
        # Get unique values
        classes = sorted(numpy.unique(array)) # get classes
        try:
            classes.remove(nodata)
        except ValueError:
            pass # nodata value couldn't be removed or wasn't set in the raster
        
        # Count number of unique cells in raster
        res = []
        for i in classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append([i.item(), int(func.count_nonzero(arr))])
        
        # Create the output layer 
        output = func.getSinkWithValues(self, parameters, self.OUTPUT_FILE, context, 
                                        values = res, 
                                        titles = ("Value","Number"),
                                        types = [TYPES_PYTHON_QVARIANT[res[0][0].__class__], QVariant.Int])
        return {self.OUTPUT_FILE: output}
        

class PatchStatistics(LandscapeStatisticsAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    METRIC = "METRIC"
    METRICsel = lcs.listStatistics()
    OUTPUT_FILE = "OUTPUT_FILE"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_patchstat.png")

    def displayName(self):
        return "Patch statistics"
    def name(self):
        return "patchstat"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))

        self.addParameter(ParameterSelection(self.METRIC, "What to calculate", self.METRICsel, 0))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        rasterlayer = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context)
        inputFilename = rasterlayer.source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        what = self.METRICsel[self.parameterAsEnum(parameters, self.METRIC, context)]

        # Processing
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array

        # Needed to see if class in inside raster
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The landscape layer %s has no valid nodata value (no number)!" % (ln)) 
        
        if Qgis.QGIS_VERSION_INT < 10900:
            pixelSize = rasterlayer.rasterUnitsPerPixel()
        else:
            pixelSize = rasterlayer.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = rasterlayer.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                raise QgsProcessingException("The cells in the landscape layer are not square. Calculated values will be incorrect")
        
        cl_analys = lcs.LandCoverAnalysis(array,pixelSize,classes)
        # Conduct the con. comp. labeling
        cl_array = numpy.copy(array) # new working array
        cl_array[cl_array!=cl] = 0
        cl_analys.f_ccl(cl_array) # CC-labeling
        res = []
        name, result = cl_analys.execSingleMetric(what,cl)                                    
        res.append([name, float(result)])
        # Create the output
        output = func.getSinkWithValues(self, parameters, self.OUTPUT_FILE, context, 
                                        values = res, 
                                        titles = ["Metric","Value"],
                                        types = [QVariant.String, QVariant.Double])
        return {self.OUTPUT_FILE: output}

            
# Calculates zonal statistics using a source and zone grid
# Output as table or raster
class ZonalStatistics(LandscapeStatisticsAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    ZONE_GRID = "ZONE_GRID"
    WHAT = "WHAT"
    m = ["mean", "sum","minimum","maximum","standard deviation","variance","median","variety"]
    CREATE_R = "CREATE_R"
    OUTPUT_FILE = "OUTPUT_FILE"
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_zonalstats.png")

    def displayName(self):
        return "Zonal statistics"
    def name(self):
        return "zonalstat"

    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterRaster(self.ZONE_GRID, "Zonal Grid", optional=False))
        self.addParameter(ParameterSelection(self.WHAT, "What to calculate", self.m, 0))
        
        self.addParameter(ParameterBoolean(self.CREATE_R, "Should a raster result be created?", False))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))  
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Raster output"))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))
        # Optionally 
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        r1 = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context)
        landFilename = r1.source()
        r2 = self.parameterAsRasterLayer(parameters, self.ZONE_GRID, context)
        zoneFilename = r2.source()
        what = self.m[self.parameterAsEnum(parameters, self.WHAT, context)]
        crR = self.parameterAsBool(parameters, self.CREATE_R, context) # should raster output be generated
        outputR = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        # Check for equal crs
        if r1.crs() != r2.crs():
            raise QgsProcessingException("Make sure both layers have the same projection")
        
        # Check for equal extent
        if r1.extent() != r2.extent():
            raise QgsProcessingException("Make sure both layers have the same extent. Use the 'Intersect Landscapes' tool beforehand!")
        
        # Start Processing
        nodata = lcs.f_returnNoDataValue(landFilename) # Get Nodata-value
        l_classes, l_array = lcs.f_landcover(landFilename,nodata) # Get classes and data array of landscape array
        z_classes, z_array = lcs.f_landcover(zoneFilename,lcs.f_returnNoDataValue(zoneFilename)) # Get classes and data array of zones array
        
        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(landFilename))
            raise QgsProcessingException("The landscape layer %s has no valid nodata value (no number)!" % (ln))        
        
        # Check for equal shape
        if l_array.shape != z_array.shape:
            raise QgsProcessingException("Make sure both layers have the same number of rows and columns. Use the 'Match two landscapes' tool beforehand!")
        
        # Construct new array by removing null-data indices from both array        
        index = numpy.where(l_array == nodata)
        # Make a copy of both layers first -> needed for optional raster creation
        l_array_orig = numpy.copy(l_array) 
        z_array_orig = numpy.copy(z_array)       
        l_array = numpy.delete(l_array, index)
        z_array = numpy.delete(z_array, index)
        
        # Get the stats
        res = []
        if what == "mean":
            out = ndimage.measurements.mean(l_array, z_array, index=z_classes)
        elif what == "sum":
            out = ndimage.measurements.sum(l_array, z_array, index=z_classes)
        elif what == "minimum":
            out = ndimage.measurements.minimum(l_array, z_array, index=z_classes)
        elif what == "maximum":
            out = ndimage.measurements.maximum(l_array, z_array, index=z_classes)
        elif what == "standard deviation":
            out = ndimage.measurements.standard_deviation(l_array, z_array, index=z_classes)
        elif what == "variance":
            out = ndimage.measurements.variance(l_array, z_array, index=z_classes)
        elif what == "median":
            out = ndimage.measurements.median(l_array, z_array, index=z_classes)
        elif what == "variety":
            #input =  [1,2,2]
            #labels = [1,2,3]            
            #out = ndimage.measurements.histogram(input, min=min(input),max=max(input),bins=1,labels=labels,index=z_classes)
            # Not working yet. Take the long road
            out = []
            for i in z_classes:
                cl_array = numpy.copy(l_array)
                if i != 0:
                    cl_array[z_array==i] = 0
                else: # use another zero value
                    cl_array[z_array==i] = -9999 #FIXME: Might not help if -9999 values are present in landscape layer. Notice user
                # Append the total number of cells minus the zero value
                out.append( len(numpy.unique(cl_array)-1) )
        
        for i in range(len(z_classes)):
            res.append([z_classes[i].item(),what,float(out[i])])

        # Create the output
        outputT = func.getSinkWithValues(self, parameters, self.OUTPUT_FILE, context, 
                                         values = res, 
                                         titles = ["Zone","Mode","Value"],
                                         types = [TYPES_PYTHON_QVARIANT[res[0][0].__class__], QVariant.String, QVariant.Double])
        
        if crR: # Should raster be created as well            
            resr = z_array_orig
            # Construct output Raster
            for i in range(len(z_classes)):
                resr[resr==z_classes[i]] = out[i] # Replace all values with zone i with the generated result
            
            # Export the raster
            func.exportRaster(resr,zoneFilename,outputR)
            return {self.OUTPUT_RASTER: outputR, self.OUTPUT_FILE: outputT}

        return {self.OUTPUT_FILE: outputT}

        
        

## Polygon Batch Overlay
from . import landscape_polygonoverlay as pov 
class RasterPolyOver(LandscapeVectorOverlayAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    VECTOR_GRID = "VECTOR_GRID"
    IS_CLASS = "IS_CLASS"
    LC_CLASS = "LC_CLASS"
    CMETRIC = "CMETRIC"
    CMETRICsel = lcs.listStatistics()
    LMETRIC = "LMETRIC"
    LMETRICsel = ["Mean", "Sum","Minimum","Maximum","Standard deviation","Lower quantile","Median","Upper quantile","Shannon Diversity Index","Eveness","Simpson Diversity Index"]
    m = ["LC_Mean","LC_Sum","LC_Min","LC_Max","LC_SD","LC_LQua","LC_Med","LC_UQua","DIV_SH","DIV_EV","DIV_SI"]
    OUTPUT_FILE = "OUTPUT_FILE"
    ADDTABLE = "ADDTABLE"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon_batchCover.png")

    def displayName(self):
        return "Overlay raster metrics (Polygons)"
    def name(self):
        return "poloverlayraster"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterVector(self.VECTOR_GRID, "Overlay Vector Grid", [QgsProcessing.TypeVectorPolygon], optional=False))
        
        self.addParameter(ParameterBoolean(self.IS_CLASS, "Raster classified?", True))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
       
        self.addParameter(ParameterSelection(self.CMETRIC, "Metrics (single class):", self.CMETRICsel, 0))
        self.addParameter(ParameterSelection(self.LMETRIC, "Metrics (landscape):", self.LMETRICsel, 0))
                
        self.addParameter(ParameterBoolean(self.ADDTABLE, "Also add to attribute table (yes)", False))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        rasterlayer = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context)
        inputFilename = rasterlayer.source()
        vectorlayer = self.parameterAsVectorLayer(parameters, self.VECTOR_GRID, context)
        vectorFilename = vectorlayer.source()
        isCl = self.parameterAsBool(parameters, self.IS_CLASS, context) # Use classified metrics per default
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        whatC = self.CMETRICsel[self.parameterAsEnum(parameters, self.CMETRIC, context)]
        whatL = self.m[self.parameterAsEnum(parameters, self.LMETRIC, context)]
        
        add2table = self.parameterAsBool(parameters, self.ADDTABLE, context)
        output = self.parameterAsVectorLayer(parameters, self.OUTPUT_FILE, context)
        
        # Make sure they have the same projection
        if rasterlayer.crs() != vectorlayer.crs():
            raise QgsProcessingException("Make sure both raster and vector layer have the same projection")

        # Processing
        bat = pov.BatchConverter(inputFilename,vectorFilename,None)
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        if nodata == None:
            raise QgsProcessingException("The landscape raster layer doesn't possess a valid nodata value")
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array
        
        if Qgis.QGIS_VERSION_INT < 10900:
            pixelSize = rasterlayer.rasterUnitsPerPixel()
        else:
            pixelSize = rasterlayer.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = rasterlayer.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                raise QgsProcessingException("The cells in the landscape layer are not square. Calculated values will be incorrect")
        
        results = []
        if isCl == True: # class metrics        
            # Needed to see if class in inside raster
            if cl not in classes:
                ln = str(path.basename(inputFilename))
                raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))
            err, r = bat.go(whatC,cl,pixelSize)
        else: # landscape metric
            err, r = bat.go(whatL,None,pixelSize)
        
        results.append(r)
        
        # Add to attribute table
        if add2table == True:
            func.addAttributesToLayer(vectorlayer,results)
        
        # Create the output layer 
        title = ["PolygonFeatureID"]
        fields = QgsFields()
        fields.append(QgsField(title[0], QVariant.Int))
        for x in results:
            fields.append(QgsField(str(x[0][1]), QVariant.Double, "", 20, 8))
        sink, output = self.parameterAsSink(parameters, self.OUTPUT_FILE, context, fields, QgsWkbTypes.NoGeometry, QgsCoordinateReferenceSystem())
        # Get number of polygon features
        feat = list(range(0,len(results[0])))
        for feature in feat: # Write feature to new line
            r = [feature]
            f = QgsFeature()
            for item in results:
                r.append(float(item[feature][2]))
            f.setAttributes(r)
            sink.addFeature(f, QgsFeatureSink.FastInsert)        
        return {self.OUTPUT_FILE: output}


# Returns the raster values below a point layer, Output Results as table
class GetRasterValuesPoint(LandscapeVectorOverlayAlgorithm):
    # Define constants
    RASTER = "RASTER"
    BAND = "BAND"
    POINT = "POINT"
    OUTPUT_FILE = "OUTPUT_FILE"
     

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_rastervalPoints.png")

    def displayName(self):
        return "Query raster values (Points)"
    def name(self):
        return "queryraster"
        
    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.RASTER, "Raster layer", optional=False))
        self.addParameter(ParameterNumber(self.BAND, "Which Raster band (1 default)", type=ParameterNumber.Integer, defaultValue=1))    
        self.addParameter(ParameterVector(self.POINT, "Point layer", [QgsProcessing.TypeVectorPoint], optional=False))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Result output", type=QgsProcessing.TypeVector))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Result output", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        r = self.parameterAsRasterLayer(parameters, self.RASTER, context)
        inputFilename = r.source()
        band = self.parameterAsInt(parameters, self.BAND, context)
        v = self.parameterAsVectorLayer(parameters, self.POINT, context)
        point = v.source()
        
        
        cr1 = v.crs()
        cr2 = r.crs()
        if cr1!=cr2:
            raise QgsProcessingException("Make sure Point and Raster layer have the same projection")

        # Use GDAL to open the raster
        raster = gdal.Open(str(inputFilename))
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        geotransform = raster.GetGeoTransform() # Get geotransform
        rproj = raster.GetProjection()
        classes, array = lcs.f_landcover(str(inputFilename)) # Get array from band 1
        raster = None # close gdal
        
        # Vector loading
        ds = ogr.Open(point)
        if (not ds):
            raise QgsProcessingException("Make sure Point layer is valid")
        lyr = ds.GetLayer()
        res = []
        for feat in lyr:
            geom = feat.GetGeometryRef()
            mx,my= geom.GetX(), geom.GetY()  #coord in map units                
            
            pp = self.mapToPixel(geotransform, mx,my)
            
            x = int(pp[0])
            y = int(pp[1])
        
            if x < 0 or y < 0 or x >= array.shape[1] or y >= array.shape[0]:
                raise QgsProcessingException("Point could not be queried or outside raster")

            res.append([feat.GetFID(), array.item(y, x)])
        
        # Create the output layer 
        output = func.getSinkWithValues(self, 
                                        parameters = parameters, 
                                        name = self.OUTPUT_FILE,
                                        context = context, 
                                        values = res, 
                                        titles = ("Point_ID","Value"),
                                        types = (QVariant.Int, TYPES_PYTHON_QVARIANT[res[0][1].__class__]))
        return {self.OUTPUT_FILE: output}
    
    def mapToPixel(self,geoMatrix, x, y):
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
    

# Overlay vector landscape layer with another polygon
class VectorPolyOver(LandscapeVectorOverlayAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    # FIXME: Maybe in the future a vector overlay will come. Don't see personal need.
    #VECTOR_GRID = "VECTOR_GRID" 
    GROUPING_ID = "GROUPING_ID"
    IS_CLASS = "IS_CLASS"
    LC_CLASS = "LC_CLASS"
    CMETRIC = "CMETRIC"
    CMETRICsel = pov.listVectorStatistics()
    LMETRIC = "LMETRIC"
    LMETRICsel = ["Mean", "Sum","Minimum","Maximum","Standard deviation","Lower quantile","Median","Upper quantile"]
    m = ["LC_Mean","LC_Sum","LC_Min","LC_Max","LC_SD","LC_LQua","LC_Med","LC_UQua"]
    OUTPUT_FILE = "OUTPUT_FILE"
    ADDTABLE = "ADDTABLE"

    
    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_vectorOverlay.png")

    def displayName(self):
        return "Overlay vector metrics (Polygons)"
    def name(self):
        return "overlayvector"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterVector(self.LAND_GRID, "Landscape Grid",[QgsProcessing.TypeVectorPolygon], optional=False))
        #self.addParameter(ParameterVector(self.VECTOR_GRID, "Overlay Vector Grid", ParameterVector.VECTOR_TYPE_POLYGON, False))
        self.addParameter(ParameterTableField(VectorPolyOver.GROUPING_ID, "Grouping ID ", VectorPolyOver.LAND_GRID))
        self.addParameter(ParameterBoolean(self.IS_CLASS, "Single class or landscape metrics", default=True))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(ParameterSelection(self.CMETRIC, "Metrics (single class):", self.CMETRICsel, 0))
        self.addParameter(ParameterSelection(self.LMETRIC, "Metrics (landscape):", self.LMETRICsel, 0))
        self.addParameter(ParameterBoolean(self.ADDTABLE, "Also add to attribute table (yes)", default=False))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))  
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context).source()
        #vectorFilename = self.parameterAs(parameters, self.VECTOR_GRID, context)
        isCl = self.parameterAsBool(parameters, self.IS_CLASS, context) # Use classified metrics per default
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        val = self.parameterAsString(parameters, self.GROUPING_ID, context)
        whatC = self.CMETRICsel[self.parameterAsEnum(parameters, self.CMETRIC, context)]
        whatL = self.m[self.parameterAsEnum(parameters, self.LMETRIC, context)]
        
        add2table = self.parameterAsBool(parameters, self.ADDTABLE, context)
            
        landlayer = Processing.getObject(inputFilename)
        #vectorlayer = Processing.getObject(vectorFilename)
                                
        # Processing
        bat = pov.VectorBatchConverter(inputFilename,vectorFilename,None)                

        results = []
        if isCl == True: # class metrics
            err, r = bat.go(whatC,cl,pixelSize)
        else: # landscape metric
            err, r = bat.go(whatL,None,pixelSize)
        
        results.append(r)
        
        # Add to attribute table
        if add2table == True:
            func.addAttributesToLayer(vectorlayer,results)
        
        # Create the output layer 
        title = ["PolygonFeatureID"]
        fields = QgsFields()
        fields.append(QgsField(title[0], QVariant.Int))
        for x in results:
            fields.append(QgsField(str(x[0][1]), QVariant.Double, "", 20, 8))
        sink, output = self.parameterAsSink(parameters, self.OUTPUT_FILE, context, fields, QgsWkbTypes.NoGeometry, QgsCoordinateReferenceSystem())
        # Get number of polygon features
        feat = list(range(0,len(results[0])))
        for feature in feat: # Write feature to new line
            r = [feature]
            f = QgsFeature()
            for item in results:
                r.append(float(item[feature][2]))
            f.setAttributes(r)
            sink.addFeature(f, QgsFeatureSink.FastInsert)        
        return {self.OUTPUT_FILE: output}


## Landscape Modifier algorithms
from . import landscape_modifier as lmod
# Conducts a connected component labeling and 
# assigns a new number to every landscape patch of a given class
class LabelLandscapePatches(LandscapeModificationAlgorithm):
    # Define constants
    LAND = "LAND"
    LC_CLASS = "LC_CLASS"
    OUTPUT_RASTER = "OUTPUT_RASTER"
    

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_label.png")

    def displayName(self):
        return "Label Landscape patches"
    def name(self):
        return "labellandscape"
    

    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND, "Classified raster layer", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Result output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND, context).source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)        
                
        # Processing
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        classes, array = lcs.f_landcover(str(inputFilename)) # get classes and array

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))
            
        # Build 
        cl_array = numpy.copy(array)
        cl_array[cl_array!=int(cl)] = 0

        struct = scipy.ndimage.generate_binary_structure(2,2)
        results, numpatches = ndimage.label(cl_array,struct) 
    
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)
        return {self.OUTPUT_RASTER: output}


# Conducts neighbourhood analysis based on a moving window approach
class NeighbourhoodAnalysis(LandscapeModificationAlgorithm):
    # Define constants
    RASTER = "RASTER"
    METHOD = "METHOD"
    SIZE = "SIZE"
    METHODsel = ["mean", "sum","minimum","maximum","standard deviation","variance","median","variety"]
    MODE = "MODE"
    m = ["reflect", "constant", "nearest", "mirror", "wrap"]
    OUTPUT_FILE = "OUTPUT_FILE"
     

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_neighboranalysis.png")

    def displayName(self):
        return "Neighbourhood Analysis (Moving Window)"
    def name(self):
        return "nanalysis"

        
    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.RASTER, "Raster layer", optional=False))
        self.addParameter(ParameterSelection(self.METHOD, "What to calculate", self.METHODsel, 0))
        self.addParameter(ParameterNumber(self.SIZE, "Neighbourhood Size", type=ParameterNumber.Integer, defaultValue=3))
        self.addParameter(ParameterSelection(self.MODE, "Behaviour at Edges", self.m, 0))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_FILE, "Result output"))  
        self.addOutput(OutputRaster(self.OUTPUT_FILE, "Result output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        rasterlayer = self.parameterAsRasterLayer(parameters, self.RASTER, context)
        inputFilename = rasterlayer.source()
        what = self.METHODsel[self.parameterAsEnum(parameters, self.METHOD, context)]
        mode = self.m[self.parameterAsEnum(parameters, self.MODE, context)]
        size = self.parameterAsInt(parameters, self.SIZE, context)
        output = self.parameterAsRasterLayer(parameters, self.OUTPUT_FILE, context)

        # Processing
        # Use GDAL to open the raster
        raster = gdal.Open(str(inputFilename))
        self.nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        self.classes, array = lcs.f_landcover(str(inputFilename))
        raster = None # close gdal
        
        # Check for nodata value
        if self.nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))
        # Format nodata to numpy.nan
        array[array==self.nodata] = numpy.nan

        if what=="mean":
            result = ndimage.generic_filter(array, numpy.mean, size=size, mode=mode)
        elif what =="sum":
            result = ndimage.generic_filter(array, numpy.sum, size=size, mode=mode)
        elif what =="minimum":
            result = ndimage.generic_filter(array, numpy.min, size=size, mode=mode)
        elif what =="maximum":
            result = ndimage.generic_filter(array, numpy.max, size=size, mode=mode)
        elif what =="standard deviation":
            result = ndimage.generic_filter(array, numpy.std, size=size, mode=mode)
        elif what =="variance":
            result = ndimage.generic_filter(array, numpy.var, size=size, mode=mode)
        elif what =="median":
            result = ndimage.generic_filter(array, numpy.median, size=size, mode=mode)
        elif what == "variety":
            result = ndimage.generic_filter(array, self.variety, size=size, mode=mode)
        #elif what =="diversity":
        #    result = ndimage.generic_filter(array, self.shannon_diversity, size=size, mode=mode)
            
        # Create the output layer 
        func.exportRaster(result,inputFilename,output,self.nodata)
        return {self.OUTPUT_FILE: output}

    # Return number of unique classes
    def variety(self,array):
        r = numpy.unique(array)
        return len(r)
    
    # To slow to be practical
    def shannon_diversity(self,array):
        sh = []
        cl_array = numpy.copy(array) # create working array
        cl_array[cl_array==int(self.nodata)] = 0
        for cl in self.classes:
            res = []
            for i in self.classes:
                arr = numpy.copy(array)
                arr[array!=i] = 0
                res.append(func.count_nonzero(arr))
            arr = numpy.copy(array)
            arr[array!=cl] = 0
            try:
                prop = func.count_nonzero(arr) / float(sum(res))
            except ZeroDivisionError: # Local cells are 0 --> all cells equal
                prop = 1
            try:
                r = prop * math.log(prop)
            except ValueError: # Local diversity is 0 --> all cells equal
                r = 0
            sh.append(r)
        return sum(sh)*-1
    

class IncreaseLandPatch(LandscapeModificationAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    TAXICAB = "TAXICAB"
    INCorDEC = "INCorDEC"
    INCDECsel = ["Increase", "Decrease"]
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_IncDec.png")

    def displayName(self):
        return "Increase/Decrease Patches"
    def name(self):
        return "incdecpatch"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        
        self.addParameter(ParameterSelection(self.INCorDEC, "What", self.INCDECsel, 0))
        self.addParameter(ParameterNumber(self.TAXICAB, "Taxicab size", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Raster output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context).source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        what = self.parameterAsEnum(parameters, self.INCorDEC, context)
        amount = self.parameterAsInt(parameters, self.TAXICAB, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
                
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))        

        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.InDecPatch(what,amount)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)
        return {self.OUTPUT_RASTER: output}


class ExtractEdges(LandscapeModificationAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    TAXICAB = "TAXICAB"
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_EdgeExtract.png")

    def displayName(self):
        return "Extract Patch edges"
    def name(self):
        return "patchedges"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(ParameterNumber(self.TAXICAB, "Taxicab size", type=ParameterNumber.Integer, defaultValue=1))        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Raster output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context).source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        amount = self.parameterAsInt(parameters, self.TAXICAB, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
                
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))

        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.extractEdges(amount)
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)
        return {self.OUTPUT_RASTER: output}


class IsolateExtremePatch(LandscapeModificationAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    WHAT = "WHAT"
    WHATsel = ["Minimum", "Maximum"]
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_MaxMin.png")

    def displayName(self):
        return "Isolate smallest/greatest Patches"
    def name(self):
        return "minmaxpatch"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        
        self.addParameter(ParameterSelection(self.WHAT, "What", self.WHATsel, 0))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Raster output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context).source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        what = self.parameterAsEnum(parameters, self.WHAT, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
                
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))
        
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        if what == 0:
            which = "min"
        else:
            which = "max"
        results = mod.getPatch(which)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)
        return {self.OUTPUT_RASTER: output}

        
class CloseHoles(LandscapeModificationAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_closeHole.png")

    def displayName(self):
        return "Close holes in patches"
    def name(self):
        return "closeholes"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Raster output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context).source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
        
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))
        
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.closeHoles()
         
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)
        return {self.OUTPUT_RASTER: output}


class CleanSmallPixels(LandscapeModificationAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    TAXICAB = "TAXICAB"
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def icon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_CleanRas.png")

    def displayName(self):
        return "Clean small pixels in patches"
    def name(self):
        return "cleanlandscape"


    def initAlgorithm(self, config):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", optional=False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", type=ParameterNumber.Integer, defaultValue=1))
        self.addParameter(ParameterNumber(self.TAXICAB, "Taxicab size", type=ParameterNumber.Integer, defaultValue=1))        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, "Raster output"))  
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, parameters, context, feedback):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.parameterAsRasterLayer(parameters, self.LAND_GRID, context).source()
        cl = self.parameterAsInt(parameters, self.LC_CLASS, context)
        amount = self.parameterAsInt(parameters, self.TAXICAB, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)
        
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no valid nodata value (no number)!" % (ln))
        
        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise QgsProcessingException("The layer %s has no cells with value %s !" % (ln,cl))
        
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.cleanRaster(amount)
         
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)
        return {self.OUTPUT_RASTER: output}

        