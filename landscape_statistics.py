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
## IMPORT ##
# Import PyQT bindings
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *
#from qgis.analysis import *

# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect

# Import numpy and scipy
import numpy
try:
    import scipy
except ImportError:
    QMessageBox.critical(QDialog(),"LecoS: Warning","Please install scipy (http://scipy.org/) in your QGIS python path.")
    sys.exit(0)
from scipy import ndimage # import ndimage module seperately for easy access
from scipy import spatial # Import spatial for average distance

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
#if hasattr(gdal,"AllRegister"): # Can register drivers
#    gdal.AllRegister() # register all gdal drivers
#if hasattr(ogr,"RegisterAll"):
#    ogr.RegisterAll() # register all ogr drivers

# BUG
# Try to use exceptions with gdal and ogr
# if hasattr(gdal,"UseExceptions"):
#     gdal.UseExceptions()
# if hasattr(ogr,"UseExceptions"):
#     ogr.UseExceptions()

helpdir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/LecoS/metric_info/"
tmpdir = tempfile.gettempdir()

## CODE START ##
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
    functionList.append(unicode("Median patch area")) # Return Median Patch area
    functionList.append(unicode("Largest Patch Index")) # Return Largest patch Index
    #functionList.append(unicode("Mean patch distance")) # Return Mean Patch distance
    #functionList.append(unicode("Mean patch perimeter")) # Return Mean Patch perimeter
    #functionList.append(unicode("Fractal Dimension Index")) # Return Fractal Dimension Index
    functionList.append(unicode("Mean patch shape ratio")) # Return Mean Patch shape
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
    
    # Alternative count_nonzero function from scipy if available
    def count_nonzero(self,array):
        if hasattr(numpy,'count_nonzero'):
            return numpy.count_nonzero(array)
        elif hasattr(scipy,'count_nonzero'):
            return scipy.count_nonzero(array)
        else:
            return (array != 0).sum()

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
        elif(name == unicode("Median patch area")):
            return unicode(name), self.f_returnPatchArea(self.cl_array,self.labeled_array,self.numpatches,"median")
        elif(name == unicode("Mean patch distance")):
            return unicode(name), self.f_returnAvgPatchDist(self.cl_array,self.numpatches)
        elif(name == unicode("Largest Patch Index")):
            return unicode(name), self.f_returnLargestPatchIndex(self.cl_array,self.labeled_array,self.numpatches)
        elif(name == unicode("Mean patch perimeter")):
            return unicode(name), self.f_returnAvgPatchPerimeter(self.labeled_array)
        elif(name == unicode("Fractal Dimension Index")):
            return unicode(name), self.f_getFractalDimensionIndex(self.labeled_array,self.numpatches)
        elif(name == unicode("Mean patch shape ratio")):
            return unicode(name), self.f_returnAvgShape(self.labeled_array,self.cl_array,self.numpatches)
        elif(name == unicode("Overall Core area")):
            return unicode(name), self.f_getCoreArea(self.labeled_array)
        elif(name == unicode("Landscape division")):
            return unicode(name), self.f_returnLandscapeDivisionIndex(self.array,self.labeled_array,self.numpatches,cl)
        elif(name == unicode("Splitting Index")):
            return unicode(name), self.f_returnSplittingIndex(self.array,self.numpatches,self.labeled_array,cl)
        elif(name == unicode("Effective Meshsize")):
            return unicode(name), self.f_returnEffectiveMeshSize(self.array,self.labeled_array,self.numpatches,cl)
        else:
            return None, None
        
    # Connected component labeling function
    def f_ccl(self,cl_array,s=2):
        # Binary structure
        self.cl_array = cl_array
        struct = scipy.ndimage.generate_binary_structure(s,s)
        self.labeled_array, self.numpatches = ndimage.label(cl_array,struct) 
        
    ## Landscape Metrics
    def execLandMetric(self,name,nodata):        
        if name == "LC_Mean":            
            return unicode(name), numpy.mean(self.array[self.array!=nodata],dtype=numpy.float64)       
        if name == "LC_Sum":
            return unicode(name), numpy.sum(self.array[self.array!=nodata],dtype=numpy.float64)
        if name == "LC_Min":
            return unicode(name), numpy.min(self.array[self.array!=nodata],dtype=numpy.float64)
        if name == "LC_Max":
            return unicode(name), numpy.max(self.array[self.array!=nodata],dtype=numpy.float64)
        if name == "LC_SD":
            return unicode(name), numpy.std(self.array[self.array!=nodata],dtype=numpy.float64)
        if name == "LC_LQua":
            return unicode(name), scipy.percentile(self.array[self.array!=nodata],25)
        if name == "LC_Med":
            return unicode(name), numpy.median(self.array[self.array!=nodata],dtype=numpy.float64)
        if name == "LC_UQua":
            return unicode(name), scipy.percentile(self.array[self.array!=nodata],75)
        if name == "DIV_SH":
            if len(self.classes) == 1:
                func.DisplayError(self.iface,"LecoS: Warning" ,"This tool needs at least two landcover classes to calculate landscape diversity!","WARNING")
                return unicode(name), "NaN"
            else:
                return unicode(name), self.f_returnDiversity("shannon",nodata)
        if name == "DIV_EV":
            if len(self.classes) == 1:
                func.DisplayError(self.iface,"LecoS: Warning" ,"This tool needs at least two landcover classes to calculate landscape diversity!","WARNING")
                return unicode(name), "NaN"
            else:
                return unicode(name), self.f_returnDiversity("eveness",nodata)
        if name == "DIV_SI":
            if len(self.classes) == 1:
                func.DisplayError(self.iface,"LecoS: Warning" ,"This tool needs at least two landcover classes to calculate landscape diversity!","WARNING")
                return unicode(name), "NaN"
            else:
                return unicode(name), self.f_returnDiversity("simpson",nodata)
    
    # Calculates a Diversity Index    
    def f_returnDiversity(self,index,nodata):
        if(index=="shannon"):
            sh = []
            cl_array = numpy.copy(self.array) # create working array
            cl_array[cl_array==int(nodata)] = 0
            for cl in self.classes:
                res = []
                for i in self.classes:
                    if i == 0: # If class 0 exists
                        arr = numpy.zeros_like(self.array)
                        arr[self.array==i] = 1
                    else:
                        arr = numpy.copy(self.array)
                        arr[self.array!=i] = 0
                    res.append(self.count_nonzero(arr))
                if cl == 0: # If class 0 exists
                    arr = numpy.zeros_like(self.array)
                    arr[self.array==cl] = 1
                else:
                    arr = numpy.copy(self.array)
                    arr[self.array!=cl] = 0
                prop = self.count_nonzero(arr) / float(sum(res))
                sh.append(prop * math.log(prop))
            return sum(sh)*-1
        elif(index=="simpson"):
            si = []
            cl_array = numpy.copy(self.array) # create working array
            cl_array[cl_array==int(nodata)] = 0
            for cl in self.classes:
                res = []
                for i in self.classes:                    
                    if i == 0: # If class 0 exists
                        arr = numpy.zeros_like(self.array)
                        arr[self.array==i] = 1
                    else:
                        arr = numpy.copy(self.array)
                        arr[self.array!=i] = 0                    
                    res.append(self.count_nonzero(arr))
                if cl == 0: # If class 0 exists
                    arr = numpy.zeros_like(self.array)
                    arr[self.array==cl] = 1
                else:
                    arr = numpy.copy(self.array)
                    arr[self.array!=cl] = 0
                prop = self.count_nonzero(arr) / float(sum(res))
                si.append(math.pow(prop,2))
            return 1-sum(si)
        elif(index=="eveness"):
            return self.f_returnDiversity("shannon",nodata) / math.log(len(self.classes))
    
    
    ## Class Metrics
    # Return the total area for the given class
    def f_returnArea(self,labeled_array):
        #sizes = scipy.ndimage.sum(array, labeled_array, range(numpatches + 1)).astype(labeled_array.dtype)
        area = self.count_nonzero(labeled_array) * self.cellsize_2
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
        self.f_LandscapeArea() # Calculate LArea
        try:
            val = (float(numpatches) / float(self.Larea))
        except ZeroDivisionError:
            val = None
        return val
    
    # Return array with a specific labeled patch
    def f_returnPatch(self,labeled_array,patch):
        # Make an array of zeros the same shape as `a`.
        feature = numpy.zeros_like(labeled_array, dtype=int)
        feature[labeled_array == patch] = 1
        return feature

    # The largest patch index
    def f_returnLargestPatchIndex(self,cl_array,labeled_array,numpatches):
        ma = self.f_returnPatchArea(cl_array,labeled_array,numpatches,"max")
        self.f_LandscapeArea()
        return ( ma / self.Larea ) * 100
  
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
                res.append(self.count_nonzero(n))
        return sum(res)
    
        import matplotlib.pyplot as plt
        plt.imshow(feature,interpolation='nearest')
        plt.axis('on')
        plt.show()
        print a[2]
    
        s = ndimage.generate_binary_structure(2,2)
        a = numpy.zeros((6,6), dtype=numpy.int)
        for i in range(0,6):
            a[i,i] = 1
        print a
        c = ndimage.binary_dilation(a,s).astype(a.dtype)
        print c
        b = c - a
        print b
        c = ndimage.distance_transform_cdt(a == 0,metric='taxicab') == 1
        c = c.astype(int)
        plt.imshow(a,interpolation='nearest')
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
        self.f_LandscapeArea() # Calculate LArea
        try:
            val = float(self.f_returnEdgeLength(labeled_array)) / float(self.Larea)
        except ZeroDivisionError:
            val = None
        return val
    
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
    
    # Calculates the Fractal dimension index patchwise
    # Returns a list with all values
    def f_getFractalDimensionIndex(self,labeled_array,numpatches):
        # Calculate patchwise
        frac = numpy.array([]).astype(float)
        for i in xrange(1,numpatches + 1): # Very slow!
            feature = self.f_returnPatch(labeled_array,i)
            a = float( self.f_returnArea(feature) )
            p = float( self.f_returnEdgeLength(feature) )
            fdi = ( 2.0 * math.log( 0.25 * p ) ) / math.log( a )
            frac = numpy.append(frac,fdi)        
        return frac
    
    # Return greatest, smallest or mean patch area
    def f_returnPatchArea(self,cl_array,labeled_array,numpatches,what):
        sizes = ndimage.sum(cl_array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        if len(sizes) != 0:            
            if what=="max":
                return (numpy.max(sizes)*self.cellsize_2) / int(self.cl)
            elif what=="min":
                return (numpy.min(sizes)*self.cellsize_2) / int(self.cl)
            elif what=="mean":
                return (numpy.mean(sizes)*self.cellsize_2) / int(self.cl)
            elif what=="median":
                return (numpy.median(sizes)*self.cellsize_2) / int(self.cl)
        else:
            return None
            
    # Returns the proportion of the labeled class in the landscape
    def f_returnProportion(self,array,cl):
        res = []
        for i in self.classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append(self.count_nonzero(arr))
        arr = numpy.copy(array)
        arr[array!=cl] = 0
        try:
            prop = self.count_nonzero(arr) / float(sum(res))
        except ZeroDivisionError:
            prop = None
        return prop
    
    # Returns the total number of cells in the array
    def f_returnTotalCellNumber(self,array):
        return int(self.count_nonzero(array))
        
    # Returns a tuple with the position of the largest patch
    # FIXME: Obsolete! Maybe leave for later use
    def f_returnPosLargestPatch(self,labeled_array):
        return numpy.unravel_index(labeled_array.argmax(),labeled_array.shape)
    
    # Get average distance between landscape patches
    def f_returnAvgPatchDist(self,cl_array,numpatches):
        if numpatches == 1:
            return 0
        else:
            #b = spatial.distance.pdist(cl_array,metric="euclidean")

            # Extract basic edge skeleton
            edge = ndimage.distance_transform_edt(cl_array == 0) == 1
            #straight_line_distance = sqrt ( ( x2 - x1 )**2 + ( y2 - y1 )**2 ); 
            x,y = numpy.where(edge)
            coords = numpy.vstack((x,y)).T
            
            b = spatial.distance.pdist(coords, lambda u, v: numpy.sqrt( ( ((u-v)*self.cellsize)**2).sum() ) )
            #b = spatial.distance.squareform(b)
            #b[b==0] = numpy.nan

            return numpy.nanmax(b) / self.cellsize # Get mean distance 
        
    # Get average Patch Perimeter of given landscape patch
    # FIXME: can't be right
    def f_returnAvgPatchPerimeter(self,labeled_array):
        labeled_array = self.f_setBorderZero(labeled_array) # add a border of zeroes
        AvgPeri = numpy.mean(labeled_array[:,1:] != labeled_array[:,:-1]) + numpy.mean(labeled_array[1:,:] != labeled_array[:-1,:])
        return AvgPeri * self.cellsize 
    
    # Average shape (ratio perimeter/area) of each patches of each lc-class
    def f_returnAvgShape(self,labeled_array,cl_array, numpatches):        
        perim = numpy.array([]).astype(float)
        for i in xrange(1,numpatches + 1): # Very slow!
                feature = self.f_returnPatch(labeled_array,i)
                p = numpy.sum(feature[:,1:] != feature[:,:-1]) + numpy.sum(feature[1:,:] != feature[:-1,:])
                perim = numpy.append(perim,p)        
        area = ndimage.sum(cl_array, labeled_array, range(numpatches + 1)).astype(float)
        area = area[area !=0]
        d = numpy.divide(perim,area).astype(float)
        return numpy.mean(d)

    # Returns the Landscape division Index for the given array
    def f_returnLandscapeDivisionIndex(self,array,labeled_array,numpatches,cl):
        res = []
        for i in self.classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append(self.count_nonzero(arr))
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
        self.f_LandscapeArea() # Calculate LArea
        res = []
        sizes = ndimage.sum(array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        for i in sizes:
            area = (i*self.cellsize_2) / int(cl)
            val = math.pow(area,2)
            res.append(val)
        area = sum(res)
        larea2 = math.pow(self.Larea,2)
        if area != 0:
            si = float(larea2) / float(area)
        else:
            si = None
        return si
    
    # Returns the Effective Mesh Size Index for the given array
    def f_returnEffectiveMeshSize(self,array,labeled_array,numpatches,cl):
        self.f_LandscapeArea() # Calculate LArea
        res = []
        sizes = ndimage.sum(array,labeled_array,range(1,numpatches+1))
        sizes = sizes[sizes!=0] # remove zeros
        for i in sizes:
            area = (i*self.cellsize_2) / int(cl)
            res.append(math.pow(area,2))            
        Earea = sum(res)
        try:
            eM = float(Earea) / float(self.Larea)
        except ZeroDivisionError:
            eM = None
        return eM
        
     
    def testing_def(self):
        #Teststuff
        pass
#         rasterPath = "/home/martin/Projekte/Bialowieza_TestData/fc.tif" 
#         srcImage = gdal.Open(str(rasterPath))
#         array = srcImage.GetRasterBand(1).ReadAsArray() # Convert first band to array
#         cl_array = numpy.copy(array)
#         cl_array[array!=1] = 0
#         s = ndimage.generate_binary_structure(2,2)
#         labeled_array, numpatches = ndimage.label(cl_array,s)
#         (upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size) = srcImage.GetGeoTransform()
#         
#         import matplotlib.pyplot as plt
#         plt.imshow(cl_array,interpolation='nearest')
#         plt.axis('on')
#         plt.show()
# 
# 
#         import numpy
#         from scipy import ndimage
#         import matplotlib.pyplot as plt
#         
#         rasterPath = "/home/martin/Projekte/Bialowieza_TestData/fc_raster.tif"
#         raster = gdal.Open(str(rasterPath))
#         array = raster.GetRasterBand(1).ReadAsArray()
#         
#         
#         landPath = "/home/martin/Projekte/Bialowieza_TestData/buffers_plot23.shp"
#         datasource = ogr.Open(str(landPath))
#         layer = datasource.GetLayer(0)
#         layerName = layer.GetName()
#         for i in range(0,layer.GetFeatureCount()):
#            f = layer.GetFeature(i)
#            print (f.GetField(0))
# 
#         a = BatchConverter(rasterPath,landPath)
#         print a.go("LC_Sum",None)
# 
#         a = numpy.zeros((6,6), dtype=numpy.int) 
#         a[1:5, 1:5] = 1;a[3,3] = 0 ; a[2,2] = 2
# 
#         s = ndimage.generate_binary_structure(2,2) # Binary structure
#         #.... Calculate Sum of 
#         b = a[1:-1, 1:-1]
#         print(numpy.exp(ndimage.convolve(numpy.log(b), s, mode = 'constant')))
#         result_array = numpy.zeros_like(a)
