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
# Import PyQT bindings
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *
# QGIS utils
import qgis.utils

# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect
from os import path

# Import functions and metrics
import lecos_functions as func

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

## Landscape preperation
# Creates a random landscape from a given distribution
class CreateRandomLandscape(GeoAlgorithm):
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

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_randomdistribution.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
       
        self.name = "Create random Landscape (Distribution)"
        self.cmdName = "createrandomraster"
        self.group = "Landscape preparation"
        
        self.addParameter(ParameterSelection(self.WHAT, "Choose value distribution", self.w, 0))
        self.addParameter(ParameterExtent(self.EXTENT, "New extent",False))
        self.addParameter(ParameterNumber(self.MIN, "Minimum / Alpha", 1, None, 1))
        self.addParameter(ParameterNumber(self.MAX, "Maximum / Beta", 1, None, 10))
        self.addParameter(ParameterNumber(self.MEAN, "Mean / Number", 1, None, 5))
        self.addParameter(ParameterNumber(self.STD, "Standard Deviation / Probability", 1, None, 2))
        self.addParameter(ParameterNumber(self.CELL_SIZE, "New cell size", 1, None, 25))    
        self.addOutput(OutputRaster(self.OUTPUT_FILE, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        what = self.w[self.getParameterValue(self.WHAT)]
        ext = self.getParameterValue(self.EXTENT)
        try:
            ext = string.split(ext,",") # split 
        except AttributeError: # Extent was empty, raise error
            raise GeoAlgorithmExecutionException("Please set an extent for the generated raster")
        mini = self.getParameterValue(self.MIN)
        maxi = self.getParameterValue(self.MAX)
        avg = self.getParameterValue(self.MEAN)
        std = self.getParameterValue(self.STD)
        cs  =  self.getParameterValue(self.CELL_SIZE)
        output = self.getOutputValue(self.OUTPUT_FILE)
        
        # Create output layer
        xmin = float(ext[0])
        xmax = float(ext[1])
        ymin = float(ext[2])
        ymax = float(ext[3])
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
                raise GeoAlgorithmExecutionException("The Probability can not be greater than 1")
        elif what == "Geometric":
            try:            
                array = numpy.random.geometric(std,(rows,cols))
            except ValueError:
                raise GeoAlgorithmExecutionException("The Probability can not be greater than 1")
        elif what == "Negative binomial":
            try:
                array = numpy.random.negative_binomial(avg,std,(rows,cols))
            except ValueError:
                raise GeoAlgorithmExecutionException("The Probability can not be greater than 1")                
        elif what == "lognormal":
            array = numpy.random.lognormal(avg,std,(rows,cols))
        elif what == "Weibull":
            array = numpy.random.weibull(avg,(rows,cols))
                
        # Create output raster
        func.createRaster(output,cols,rows,array,nodata,gt)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None        

# Inspired from here: http://stackoverflow.com/questions/10454316/how-to-project-and-resample-a-grid-to-match-another-grid-with-gdal-python
class MatchLandscapes(GeoAlgorithm):
    # Define constants
    LAND1 = "LAND1"
    LAND2 = "LAND2"
    INTERP = "INTERP"
    i = ['Bilinear','Cubic','Cubicspline','Lanczos','NearestNeighbour']
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_matchlandscapes.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Match two landscapes"
        self.cmdName = "preplandscape"
        self.group = "Landscape preparation"

        self.addParameter(ParameterRaster(self.LAND1, "Source landscape", False))
        self.addParameter(ParameterRaster(self.LAND2, "Target landscape", False))
        self.addParameter(ParameterSelection(self.INTERP, "Interpolation mode", self.i, 0))

        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputSource = self.getParameterValue(self.LAND1)
        inputTarget = self.getParameterValue(self.LAND2)
        interp = self.i[self.getParameterValue(self.INTERP)]
        output = self.getOutputValue(self.OUTPUT_RASTER)
                
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
            raise GeoAlgorithmExecutionException("Could not generate output file")
            
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
        

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None      


class RasterWithRasterClip(GeoAlgorithm):
    # Define constants
    LAND1 = "LAND1"
    LAND2 = "LAND2"
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_clipRaster.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Intersect Landscapes"
        self.cmdName = "landintersect"
        self.group = "Landscape preparation"

        self.addParameter(ParameterRaster(self.LAND1, "Source landscape", False))
        self.addParameter(ParameterRaster(self.LAND2, "Target landscape", False))

        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputSource = self.getParameterValue(self.LAND1)
        inputTarget = self.getParameterValue(self.LAND2)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        
        # Check for equal crs
        r1 = Processing.getObject(inputSource)
        r2 = Processing.getObject(inputTarget)
        if r1.crs() != r2.crs():
            raise GeoAlgorithmExecutionException("Make sure both raster layer have the same projection")
                    
        # Processing
        src = gdal.Open(str(inputSource), gdalconst.GA_ReadOnly)
        src_proj = src.GetProjection()
        src_geotrans = src.GetGeoTransform()
        nodata = src.GetRasterBand(1).GetNoDataValue() # keep the nodata value
        wide = src.RasterXSize
        high = src.RasterYSize
        
        # r1 has left, top, right, bottom of dataset's bounds in geospatial coordinates.
        r1 = [src_geotrans[0], src_geotrans[3], src_geotrans[0] + (src_geotrans[1] * wide), src_geotrans[3] + (src_geotrans[5] * high)]

        # We want a section of source that matches this:
        match_ds = gdal.Open(str(inputTarget), gdalconst.GA_ReadOnly)
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
            raise GeoAlgorithmExecutionException("Landscape layers are not intersecting.")

        else:
            # Convert to pixels
            p1 = self.world2Pixel(src_geotrans,intersection[0],intersection[1])
            p2 = self.world2Pixel(src_geotrans,intersection[2],intersection[3])
            band = src.GetRasterBand(1)            
            result = band.ReadAsArray(p1[0], p1[1], p2[0] - p1[0], p2[1] - p1[1], p2[0] - p1[0], p2[1] - p1[1])
            
            # Write to new raster
            func.exportRaster(result,inputTarget,output,nodata)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

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
import landscape_statistics as lcs
class LandscapeStatistics(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"

    METRIC = "METRIC"
    METRICsel = ["Mean", "Sum","Minimum","Maximum","Standard deviation","Lower quantile","Median","Upper quantile","Shannon Diversity Index","Eveness","Simpson Diversity Index"]
    m = ["LC_Mean","LC_Sum","LC_Min","LC_Max","LC_SD","LC_LQua","LC_Med","LC_UQua","DIV_SH","DIV_EV","DIV_SI"]
    
    OUTPUT_FILE = "OUTPUT_FILE"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Landscape wide statistics"
        self.cmdName = "landscapestat"
        self.group = "Landscape statistics"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        
        self.addParameter(ParameterSelection(self.METRIC, "What to calculate", self.METRICsel, 0))
        
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        what = self.m[self.getParameterValue(self.METRIC)]
        output = self.getOutputValue(self.OUTPUT_FILE)
        rasterlayer = Processing.getObject(inputFilename)

        # Processing
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))
        
        if QGis.QGIS_VERSION_INT < 10900:
            pixelSize = rasterlayer.rasterUnitsPerPixel()
        else:
            pixelSize = rasterlayer.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = rasterlayer.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                raise GeoAlgorithmExecutionException("The cells in the landscape layer are not square. Calculated values will be incorrect")
        
        cl_analys = lcs.LandCoverAnalysis(array,pixelSize,classes)
        res = []
        name, result = cl_analys.execLandMetric(what,nodata)                                    
        res.append([name, result])
        # Create the output
        func.saveToCSV(res,["Metric","Value"],output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

# Lists all unique raster cells of a raster
# Returns the total number per cell in a table
class CountRasterCells(GeoAlgorithm):
    # Define constants
    RASTER = "RASTER"
    BAND = "BAND"
    OUTPUT_FILE = "OUTPUT_FILE"
     
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_countRastercells.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.name = "Count Raster Cells"
        self.cmdName = "countrastercell"
        self.group = "Landscape statistics"

        self.addParameter(ParameterRaster(self.RASTER, "Raster layer", False))
        self.addParameter(ParameterNumber(self.BAND, "Which Raster band (1 default)", 1, None, 1))      
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.RASTER)
        band = self.getParameterValue(self.BAND)
        output = self.getOutputValue(self.OUTPUT_FILE)

        # Use GDAL to open the raster
        raster = gdal.Open(str(inputFilename))
        band = raster.GetRasterBand(band)
        try:
            array =  band.ReadAsArray() 
        except ValueError:
            raise GeoAlgorithmExecutionException("Input Raster to big. Try to slize it up.")
        nodata = band.GetNoDataValue() # Get Nodata-value
        raster = None # close gdal

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))
                
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
            res.append((i,func.count_nonzero(arr)))
        
        # Create the output layer 
        func.saveToCSV(res,("Value","Number"),output)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class PatchStatistics(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    METRIC = "METRIC"
    METRICsel = lcs.listStatistics()
    
    OUTPUT_FILE = "OUTPUT_FILE"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_patchstat.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Patch statistics"
        self.cmdName = "patchstat"
        self.group = "Landscape statistics"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))

        self.addParameter(ParameterSelection(self.METRIC, "What to calculate", self.METRICsel, 0))
        
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        cl = self.getParameterValue(self.LC_CLASS)
        what = self.METRICsel[self.getParameterValue(self.METRIC)]
        output = self.getOutputValue(self.OUTPUT_FILE)
        rasterlayer = Processing.getObject(inputFilename)

        # Processing
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array

        # Needed to see if class in inside raster
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The landscape layer %s has no valid nodata value (no number)!" % (ln)) 
        
        if QGis.QGIS_VERSION_INT < 10900:
            pixelSize = rasterlayer.rasterUnitsPerPixel()
        else:
            pixelSize = rasterlayer.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = rasterlayer.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                raise GeoAlgorithmExecutionException("The cells in the landscape layer are not square. Calculated values will be incorrect")
        
        cl_analys = lcs.LandCoverAnalysis(array,pixelSize,classes)
        # Conduct the con. comp. labeling
        cl_array = numpy.copy(array) # new working array
        cl_array[cl_array!=cl] = 0
        cl_analys.f_ccl(cl_array) # CC-labeling
        res = []
        name, result = cl_analys.execSingleMetric(what,cl)                                    
        res.append([name, result])
        # Create the output
        func.saveToCSV(res,["Metric","Value"],output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None      
            

# Calculates zonal statistics using a source and zone grid
# Output as table or raster
class ZonalStatistics(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    ZONE_GRID = "ZONE_GRID"
    WHAT = "WHAT"
    m = ["mean", "sum","minimum","maximum","standard deviation","variance","median","variety"]
    CREATE_R = "CREATE_R"
    OUTPUT_FILE = "OUTPUT_FILE"
    OUTPUT_RASTER = "OUTPUT_RASTER"

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_zonalstats.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Zonal statistics"
        self.cmdName = "zonalstat"
        self.group = "Landscape statistics"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterRaster(self.ZONE_GRID, "Zonal Grid", False))
        self.addParameter(ParameterSelection(self.WHAT, "What to calculate", self.m, 0))
        
        self.addParameter(ParameterBoolean(self.CREATE_R, "Should a raster result be created?", False))
        
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file",False))
        # Optionally 
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        landFilename = self.getParameterValue(self.LAND_GRID)
        zoneFilename = self.getParameterValue(self.ZONE_GRID)
        what = self.m[self.getParameterValue(self.WHAT)]
        crR = self.getParameterValue(self.CREATE_R) # should raster output be generated
        outputT = self.getOutputValue(self.OUTPUT_FILE)
        outputR = self.getOutputValue(self.OUTPUT_RASTER)

        # Check for equal crs
        r1 = Processing.getObject(landFilename)
        r2 = Processing.getObject(zoneFilename)
        if r1.crs() != r2.crs():
            raise GeoAlgorithmExecutionException("Make sure both layers have the same projection")
        
        # Check for equal extent
        if r1.extent() != r2.extent():
            raise GeoAlgorithmExecutionException("Make sure both layers have the same extent. Use the 'Intersect Landscapes' tool beforehand!")
        
        # Start Processing
        nodata = lcs.f_returnNoDataValue(landFilename) # Get Nodata-value
        l_classes, l_array = lcs.f_landcover(landFilename,nodata) # Get classes and data array of landscape array
        z_classes, z_array = lcs.f_landcover(zoneFilename,lcs.f_returnNoDataValue(zoneFilename)) # Get classes and data array of zones array
        
        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(landFilename))
            raise GeoAlgorithmExecutionException("The landscape layer %s has no valid nodata value (no number)!" % (ln))        
        
        # Check for equal shape
        if l_array.shape != z_array.shape:
            raise GeoAlgorithmExecutionException("Make sure both layers have the same number of rows and columns. Use the 'Match two landscapes' tool beforehand!")
        
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
            res.append([z_classes[i],what,out[i]])

        # Create the output
        func.saveToCSV(res,["Zone","Mode","Value"],outputT)
        
        if crR: # Should raster be created as well            
            resr = z_array_orig
            # Construct output Raster
            for i in range(len(z_classes)):
                resr[resr==z_classes[i]] = out[i] # Replace all values with zone i with the generated result
            
            # Export the raster
            func.exportRaster(resr,zoneFilename,outputR)
        
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None


## Polygon Batch Overlay
import landscape_polygonoverlay as pov 
class RasterPolyOver(GeoAlgorithm):
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
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon_batchCover.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        self.name = "Overlay raster metrics (Polygons)"
        self.cmdName = "poloverlayraster"
        self.group = "Landscape vector overlay"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterVector(self.VECTOR_GRID, "Overlay Vector Grid", ParameterVector.VECTOR_TYPE_POLYGON, False))
        
        self.addParameter(ParameterBoolean(self.IS_CLASS, "Raster classified?", True))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
       
        self.addParameter(ParameterSelection(self.CMETRIC, "Metrics (single class):", self.CMETRICsel, 0))
        self.addParameter(ParameterSelection(self.LMETRIC, "Metrics (landscape):", self.LMETRICsel, 0))
                
        self.addParameter(ParameterBoolean(self.ADDTABLE, "Also add to attribute table (yes)", False))
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        vectorFilename = self.getParameterValue(self.VECTOR_GRID)
        isCl = self.getParameterValue(self.IS_CLASS) # Use classified metrics per default
        cl = self.getParameterValue(self.LC_CLASS)
        whatC = self.CMETRICsel[self.getParameterValue(self.CMETRIC)]
        whatL = self.m[self.getParameterValue(self.LMETRIC)]
        
        add2table = self.getParameterValue(self.ADDTABLE)
        output = self.getOutputValue(self.OUTPUT_FILE)
            
        rasterlayer = Processing.getObject(inputFilename)
        vectorlayer = Processing.getObject(vectorFilename)
        
        # Make sure they have the same projection
        if rasterlayer.crs() != vectorlayer.crs():
            raise GeoAlgorithmExecutionException("Make sure both raster and vector layer have the same projection")

        # Processing
        bat = pov.BatchConverter(inputFilename,vectorFilename,None)
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        if nodata == None:
            raise GeoAlgorithmExecutionException("The landscape raster layer doesn't possess a valid nodata value")
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array
        
        if QGis.QGIS_VERSION_INT < 10900:
            pixelSize = rasterlayer.rasterUnitsPerPixel()
        else:
            pixelSize = rasterlayer.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = rasterlayer.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                raise GeoAlgorithmExecutionException("The cells in the landscape layer are not square. Calculated values will be incorrect")
        
        results = []
        if isCl == True: # class metrics        
            # Needed to see if class in inside raster
            if cl not in classes:
                ln = str(path.basename(inputFilename))
                raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))
            err, r = bat.go(whatC,cl,pixelSize)
        else: # landscape metric
            err, r = bat.go(whatL,None,pixelSize)
        
        results.append(r)
        
        # Add to attribute table
        if add2table == True:
            func.addAttributesToLayer(vectorlayer,results)
        
        # Create the output layer 
        title = ["PolygonFeatureID"]
        for x in results:
            title.append( str(x[0][1]) ) 
        f = open(output, "wb" )
        writer = csv.writer(f,delimiter=';',quotechar="'",quoting=csv.QUOTE_ALL)
        writer.writerow(title)
        # Get number of polygon features
        feat = range(0,len(results[0]))
        for feature in feat: # Write feature to new line
            r = [feature]
            for item in results:
                r.append(item[feature][2])
            writer.writerow(r)
        f.close()        

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

# Returns the raster values below a point layer, Output Results as table
class GetRasterValuesPoint(GeoAlgorithm):
    # Define constants
    RASTER = "RASTER"
    BAND = "BAND"
    POINT = "POINT"
    OUTPUT_FILE = "OUTPUT_FILE"
     
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_rastervalPoints.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
        
        self.name = "Query raster values (Points)"
        self.cmdName = "queryraster"
        self.group = "Landscape vector overlay"
        
        self.addParameter(ParameterRaster(self.RASTER, "Raster layer", False))
        self.addParameter(ParameterNumber(self.BAND, "Which Raster band (1 default)", 1, None, 1))    
        self.addParameter(ParameterVector(self.POINT, "Point layer", ParameterVector.VECTOR_TYPE_POINT, False))
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.RASTER)
        band = self.getParameterValue(self.BAND)
        point = self.getParameterValue(self.POINT)
        output = self.getOutputValue(self.OUTPUT_FILE)
        
        r = Processing.getObject(inputFilename)
        v = Processing.getObject(point)
        cr1 = v.crs()
        cr2 = r.crs()
        if cr1!=cr2:
            raise GeoAlgorithmExecutionException("Make sure Point and Raster layer have the same projection")

        # Use GDAL to open the raster
        raster = gdal.Open(str(inputFilename))
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        geotransform = raster.GetGeoTransform() # Get geotransform
        rproj = raster.GetProjection()
        classes, array = lcs.f_landcover(str(inputFilename)) # Get array from band 1
        raster = None # close gdal
        
        # Vector loading
        ds = ogr.Open(point)
        lyr = ds.GetLayer()
        res = []
        for feat in lyr:
            geom = feat.GetGeometryRef()
            mx,my= geom.GetX(), geom.GetY()  #coord in map units                
            
            pp = self.mapToPixel(geotransform, mx,my)
            
            x = int(pp[0])
            y = int(pp[1])
        
            if x < 0 or y < 0 or x >= array.shape[1] or y >= array.shape[0]:
                raise GeoAlgorithmExecutionException("Point could not be queried or outside raster")

            res.append((feat.GetFID(),array[y, x]))
        
        # Create the output layer 
        func.saveToCSV(res,("Point_ID","Value"),output)
    
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
    
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None


# Overlay vector landscape layer with another polygon
class VectorPolyOver(GeoAlgorithm):
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
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_vectorOverlay.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Overlay vector metrics (Polygons)"
        self.cmdName = "overlayvector"
        self.group = "Landscape vector overlay"

        self.addParameter(ParameterVector(self.LAND_GRID, "Landscape Grid",ParameterVector.VECTOR_TYPE_POLYGON, False))
        #self.addParameter(ParameterVector(self.VECTOR_GRID, "Overlay Vector Grid", ParameterVector.VECTOR_TYPE_POLYGON, False))
        self.addParameter(ParameterTableField(VectorPolyOver.GROUPING_ID, "Grouping ID ", VectorPolyOver.LAND_GRID))
        self.addParameter(ParameterBoolean(self.IS_CLASS, "Single class or landscape metrics", True))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
                
        self.addParameter(ParameterSelection(self.CMETRIC, "Metrics (single class):", self.CMETRICsel, 0))
        self.addParameter(ParameterSelection(self.LMETRIC, "Metrics (landscape):", self.LMETRICsel, 0))
                
        self.addParameter(ParameterBoolean(self.ADDTABLE, "Also add to attribute table (yes)", False))
        self.addOutput(OutputTable(self.OUTPUT_FILE, "Output file"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        #vectorFilename = self.getParameterValue(self.VECTOR_GRID)
        isCl = self.getParameterValue(self.IS_CLASS) # Use classified metrics per default
        cl = self.getParameterValue(self.LC_CLASS)
        val = self.getParameterValue(self.GROUPING_ID)
        whatC = self.CMETRICsel[self.getParameterValue(self.CMETRIC)]
        whatL = self.m[self.getParameterValue(self.LMETRIC)]
        
        add2table = self.getParameterValue(self.ADDTABLE)
        output = self.getOutputValue(self.OUTPUT_FILE)
            
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
        for x in results:
            title.append( str(x[0][1]) ) 
        f = open(output, "wb" )
        writer = csv.writer(f,delimiter=';',quotechar="'",quoting=csv.QUOTE_ALL)
        writer.writerow(title)
        # Get number of polygon features
        feat = range(0,len(results[0]))
        for feature in feat: # Write feature to new line
            r = [feature]
            for item in results:
                r.append(item[feature][2])
            writer.writerow(r)
        f.close()        

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None


## Landscape Modifier algorithms
import landscape_modifier as lmod
# Conducts a connected component labeling and 
# assigns a new number to every landscape patch of a given class
class LabelLandscapePatches(GeoAlgorithm):
    # Define constants
    LAND = "LAND"
    LC_CLASS = "LC_CLASS"
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_label.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Label Landscape patches"
        self.cmdName = "labellandscape"
        self.group = "Landscape modifications"

        self.addParameter(ParameterRaster(self.LAND, "Classified raster layer", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND)
        cl = self.getParameterValue(self.LC_CLASS)
        output = self.getOutputValue(self.OUTPUT_RASTER)        
                
        # Processing
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        classes, array = lcs.f_landcover(str(inputFilename)) # get classes and array

        # Check for nodata value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))
            
        # Build 
        cl_array = numpy.copy(array)
        cl_array[cl_array!=int(cl)] = 0

        struct = scipy.ndimage.generate_binary_structure(2,2)
        results, numpatches = ndimage.label(cl_array,struct) 
    
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

# Conducts neighbourhood analysis based on a moving window approach
class NeighbourhoodAnalysis(GeoAlgorithm):
    # Define constants
    RASTER = "RASTER"
    METHOD = "METHOD"
    SIZE = "SIZE"
    METHODsel = ["mean", "sum","minimum","maximum","standard deviation","variance","median","variety"]
    MODE = "MODE"
    m = ["reflect", "constant", "nearest", "mirror", "wrap"]
    OUTPUT_FILE = "OUTPUT_FILE"
     
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_neighboranalysis.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''
       
        self.name = "Neighbourhood Analysis (Moving Window)"
        self.cmdName = "nanalysis"
        self.group = "Landscape modifications"
        
        self.addParameter(ParameterRaster(self.RASTER, "Raster layer", False))
        self.addParameter(ParameterSelection(self.METHOD, "What to calculate", self.METHODsel, 0))
        self.addParameter(ParameterNumber(self.SIZE, "Neighbourhood Size", 1, None, 3))
        self.addParameter(ParameterSelection(self.MODE, "Behaviour at Edges", self.m, 0))
        self.addOutput(OutputRaster(self.OUTPUT_FILE, "Result output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.RASTER)
        what = self.METHODsel[self.getParameterValue(self.METHOD)]
        mode = self.m[self.getParameterValue(self.MODE)]
        size = self.getParameterValue(self.SIZE)
        output = self.getOutputValue(self.OUTPUT_FILE)
        rasterlayer = Processing.getObject(inputFilename)

        # Processing
        # Use GDAL to open the raster
        raster = gdal.Open(str(inputFilename))
        self.nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        self.classes, array = lcs.f_landcover(str(inputFilename))
        raster = None # close gdal
        
        # Check for nodata value
        if self.nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))
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
    
    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class IncreaseLandPatch(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"

    TAXICAB = "TAXICAB"
    INCorDEC = "INCorDEC"
    INCDECsel = ["Increase", "Decrease"]
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_IncDec.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Increase/Decrease Patches"
        self.cmdName = "incdecpatch"
        self.group = "Landscape modifications"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
        
        self.addParameter(ParameterSelection(self.INCorDEC, "What", self.INCDECsel, 0))
        self.addParameter(ParameterNumber(self.TAXICAB, "Taxicab size", 1, None, 1))
        
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        cl = self.getParameterValue(self.LC_CLASS)
        what = self.getParameterValue(self.INCorDEC)
        amount = self.getParameterValue(self.TAXICAB)
        output = self.getOutputValue(self.OUTPUT_RASTER)
                
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))        

        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.InDecPatch(what,amount)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

class ExtractEdges(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"

    TAXICAB = "TAXICAB"
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_EdgeExtract.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Extract Patch edges"
        self.cmdName = "patchedges"
        self.group = "Landscape modifications"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
        self.addParameter(ParameterNumber(self.TAXICAB, "Taxicab size", 1, None, 1))        
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        cl = self.getParameterValue(self.LC_CLASS)
        amount = self.getParameterValue(self.TAXICAB)
        output = self.getOutputValue(self.OUTPUT_RASTER)
                
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))

        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.extractEdges(amount)
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None

        
class IsolateExtremePatch(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"

    WHAT = "WHAT"
    WHATsel = ["Minimum", "Maximum"]
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_MaxMin.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Isolate smallest/greatest Patches"
        self.cmdName = "minmaxpatch"
        self.group = "Landscape modifications"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
        
        self.addParameter(ParameterSelection(self.WHAT, "What", self.WHATsel, 0))
        
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        cl = self.getParameterValue(self.LC_CLASS)
        what = self.getParameterValue(self.WHAT)
        output = self.getOutputValue(self.OUTPUT_RASTER)
                
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))
        
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        if what == 0:
            which = "min"
        else:
            which = "max"
        results = mod.getPatch(which)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None
        
class CloseHoles(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_closeHole.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Close holes in patches"
        self.cmdName = "closeholes"
        self.group = "Landscape modifications"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        cl = self.getParameterValue(self.LC_CLASS)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))

        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))
        
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.closeHoles()
         
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None


class CleanSmallPixels(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    
    TAXICAB = "TAXICAB"

    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"img_CleanRas.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Clean small pixels in patches"
        self.cmdName = "cleanlandscape"
        self.group = "Landscape modifications"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterNumber(self.LC_CLASS, "Choose Landscape Class", 1, None, 1))
        self.addParameter(ParameterNumber(self.TAXICAB, "Taxicab size", 1, None, 1))        

        self.addOutput(OutputRaster(self.OUTPUT_RASTER, "Raster output"))

    def processAlgorithm(self, progress):
        '''Here is where the processing itself takes place'''
        
        # Retrieve the values of the parameters entered by the user
        inputFilename = self.getParameterValue(self.LAND_GRID)
        cl = self.getParameterValue(self.LC_CLASS)
        amount = self.getParameterValue(self.TAXICAB)
        output = self.getOutputValue(self.OUTPUT_RASTER)
        
        # Check for nodata value
        nodata = lcs.f_returnNoDataValue(str(inputFilename)) # Get Nodata-value
        if nodata == None:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no valid nodata value (no number)!" % (ln))
        
        # Needed to see if class in inside raster
        classes, array = lcs.f_landcover(inputFilename)
        if cl not in classes:
            ln = str(path.basename(inputFilename))
            raise GeoAlgorithmExecutionException("The layer %s has no cells with value %s !" % (ln,cl))
        
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.cleanRaster(amount)
         
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def help(self):
        helppath = os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        if os.path.isfile(helppath):
            return False, helppath
        else:
            return False, None
        