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
# Import sextante bindings
from sextante.core.GeoAlgorithm import GeoAlgorithm
from sextante.core.Sextante import Sextante
from sextante.core.SextanteUtils import SextanteUtils
from sextante.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

from sextante.outputs.OutputVector import OutputVector
from sextante.outputs.OutputRaster import OutputRaster
from sextante.outputs.OutputTable import OutputTable

from sextante.parameters.ParameterVector import ParameterVector
from sextante.parameters.ParameterRaster import ParameterRaster
from sextante.parameters.ParameterNumber import ParameterNumber
from sextante.parameters.ParameterBoolean import ParameterBoolean
from sextante.parameters.ParameterSelection import ParameterSelection

# Import PyQT bindings
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *

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
    from osgeo import ogr
except ImportError:
    import ogr

# Register gdal and ogr drivers
if hasattr(gdal,"AllRegister"): # Can register drivers
    gdal.AllRegister() # register all gdal drivers
if hasattr(ogr,"RegisterAll"):
    ogr.RegisterAll() # register all ogr drivers

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
        rasterlayer = Sextante.getObject(inputFilename)

        # Processing
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array
        
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

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")

class PatchStatistics(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    METRIC = "METRIC"
    METRICsel = lcs.listStatistics()
    
    OUTPUT_FILE = "OUTPUT_FILE"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

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
        rasterlayer = Sextante.getObject(inputFilename)

        # Processing
        nodata = lcs.f_returnNoDataValue(inputFilename) # Get Nodata-value
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array
        
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
        name, result = cl_analys.execSingleMetric(what,cl)                                    
        res.append([name, result])
        # Create the output
        func.saveToCSV(res,["Metric","Value"],output)

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")


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
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Overlay Metrics (raster)"
        self.cmdName = "overlayraster"
        self.group = "Landscape polygon overlay"

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
            
        rasterlayer = Sextante.getObject(inputFilename)
        vectorlayer = Sextante.getObject(vectorFilename)
                                
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
            err, r = bat.go(whatC,cl,pixelSize)
        else: # landscape metric
            err, r = bat.go(whatL,None,pixelSize)
        
        results.append(r)
        
        # Add to attribute table
        if add2table == True:
            func.addAttributesToLayer2(vectorlayer,results)
        
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

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")

class VectorPolyOver(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
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
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

    def defineCharacteristics(self):
        '''Here we define the inputs and output of the algorithm, along
        with some other properties'''

        self.name = "Overlay Metrics (vector)"
        self.cmdName = "overlayvector"
        self.group = "Landscape polygon overlay"

        self.addParameter(ParameterRaster(self.LAND_GRID, "Landscape Grid", False))
        self.addParameter(ParameterSelection(self.GROUPING_ID, "Grouping ID of vector layer", self.CMETRICsel, 0))
        #self.addParameter(ParameterVector(self.VECTOR_GRID, "Overlay Vector Grid", ParameterVector.VECTOR_TYPE_POLYGON, False))
        
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
            
        landlayer = Sextante.getObject(inputFilename)
        vectorlayer = Sextante.getObject(vectorFilename)
                                
        # Processing
        bat = pov.BatchConverter(inputFilename,vectorFilename,None)
        classes, array = lcs.f_landcover(inputFilename,nodata) # Get classes and data array
                
        results = []
        if isCl == True: # class metrics
            err, r = bat.go(whatC,cl,pixelSize)
        else: # landscape metric
            err, r = bat.go(whatL,None,pixelSize)
        
        results.append(r)
        
        # Add to attribute table
        if add2table == True:
            func.addAttributesToLayer2(vectorlayer,results)
        
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

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")

## Landscape Modifier algorithms
import landscape_modifier as lmod
class IncreaseLandPatch(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"

    TAXICAB = "TAXICAB"
    INCorDEC = "INCorDEC"
    INCDECsel = ["Increase", "Decrease"]
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

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
                
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.InDecPatch(what,amount)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")

class ExtractEdges(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"

    TAXICAB = "TAXICAB"
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

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
                
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.extractEdges(amount)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        
class IsolateExtremePatch(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"

    WHAT = "WHAT"
    WHATsel = ["Minimum", "Maximum"]
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

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
                
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        if what == 0:
            which = "min"
        else:
            which = "max"
        results = mod.getPatch(which)
        
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        
class CloseHoles(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    
    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

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
                
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.closeHoles()
         
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")

class CleanSmallPixels(GeoAlgorithm):
    # Define constants
    LAND_GRID = "LAND_GRID"
    LC_CLASS = "LC_CLASS"
    
    TAXICAB = "TAXICAB"

    OUTPUT_RASTER = "OUTPUT_RASTER"
    
    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")

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
                
        # Processing
        mod = lmod.LandscapeMod(inputFilename,cl)
        results = mod.cleanRaster(amount)
         
        # Create the output layer 
        func.exportRaster(results,inputFilename,output)

    def helpFile(self):
        return os.path.join(os.path.dirname(__file__), "sextante_info", self.cmdName + ".html")
        