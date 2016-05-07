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

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *
#from qgis.analysis import *

# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect
from os import path

# Import landscape functions
import landscape_statistics as lcs

# Import numpy and scipy
import numpy
try:
    import scipy
except ImportError:
    QMessageBox.critical(QDialog(),"LecoS: Warning","Please install scipy (http://scipy.org/) in your QGIS python path.")
    sys.exit(0)
from scipy import ndimage # import ndimage module seperately for easy access

# Try to import PIL
try:
    try:
        import Image, ImageDraw
    except ImportError:
        from PIL import Image, ImageDraw
except ImportError:
    QMessageBox.critical(QDialog(),"LecoS: Warning","You need to have the image library PIL installed.")
    sys.exit(0)

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
# # Try to use exceptions with gdal and ogr
# if hasattr(gdal,"UseExceptions"):
#     gdal.UseExceptions()
# if hasattr(ogr,"UseExceptions"):
#     ogr.UseExceptions()

## CODE START ##
# Many functions stolen from here :-)
# http://geospatialpython.com/2011/02/clip-raster-using-shapefile.html
class BatchConverter():
    def __init__(self,rasterPath,vectorPath,iface=None):
        # load as a gdal image to get geotransform and full array
        self.srcImage = gdal.Open(str(rasterPath))
        band = self.srcImage.GetRasterBand(1)
        self.nodata = band.GetNoDataValue()
        if self.nodata == None:
            print "Nodata-value is not specified in the raster layer"
            self.nodata = 0

        self.geoTrans = self.srcImage.GetGeoTransform()
        try:
            self.srcArray = self.srcImage.GetRasterBand(1).ReadAsArray() # Convert first band to array
        except ValueError:
            QMessageBox.warning(QDialog(),"LecoS: Warning","Raster file is to big for processing. Please crop the file and try again.")
            return
        # Create an OGR layer from a boundary shapefile used to clip
        self.shapef = ogr.Open("%s" % str(vectorPath))
        self.lyr = self.shapef.GetLayer()

        # Raster extent
        ext = self.GetExtent(self.geoTrans,self.srcImage.RasterXSize,self.srcImage.RasterYSize)
        self.extent = (ext[0][0],ext[2][0],ext[1][1],ext[0][1]) # Format to the same tuple structure as the vector layer
        # Failure Clip counter
        self.featFailed = []

        # Interface to QGIS
        self.iface = iface

        # Error Counter
        self.error = 0

    # Alternative count_nonzero function from scipy if available
    def count_nonzero(self,array):
        if hasattr(numpy,'count_nonzero'):
            return numpy.count_nonzero(array)
        elif hasattr(scipy,'count_nonzero'):
            return scipy.count_nonzero(array)
        else:
            return (array != 0).sum()

    #Iterate through all features and executes the named command
    #Values are returned as array per feature
    def go(self,cmd,cl,cellsize=1,landID=None,rasE=None):
        res = []
        for i in xrange(0,self.lyr.GetFeatureCount()):
            if self.lyr.GetFeatureCount() == 1:
                poly = self.lyr.GetFeature(0)
            else:
                poly = self.lyr.GetFeature(i)

            # Test if polygon feature is inside raster extent, otherwise return None as result
            #geom = poly.GetGeometryRef()
            #f_coord = geom.GetEnvelope()
            #ints = self.BBoxIntersect(self.extent,f_coord)
            #if ints: # Bounding Box intersecting ?
            array = self.getClipArray(poly)
            if array != None: # Multi polygon or no raster values below ?
                classes = sorted(numpy.unique(array)) # get classes
                for val in (self.nodata,0):# Remove raster nodata value and zeros from class list
                    try:
                        classes.remove(val)
                    except ValueError:
                        pass
                # Classified Methods -> Use landscape_statistics module
                if cl != None:
                    cl_analys = lcs.LandCoverAnalysis(array,cellsize,classes)
                    cl_array = numpy.copy(array) # new working array
                    cl_array[cl_array!=cl] = 0
                    cl_analys.f_ccl(cl_array) # CC-labeling
                    name, r = cl_analys.execSingleMetric(cmd,cl)
                    # Get FieldValue of given Field
                    #id = self.getFieldValue(poly,landID)
                    id = poly.GetFID()
                    b = [id,name,r]
                    res.append(b)
                # Unclassified Methods
                else:
                    if(cmd == "LC_Sum"):
                        r = self.returnArraySum(array)
                    elif(cmd == "LC_Mean"):
                        r = self.returnArrayMean(array)
                    elif(cmd == "LC_SD"):
                        r = self.returnArrayStd(array)
                    elif(cmd == "LC_Med"):
                        r = self.returnArrayMedi(array)
                    elif(cmd == "LC_Max"):
                        r = self.returnArrayMax(array)
                    elif(cmd == "LC_Min"):
                        r = self.returnArrayMin(array)
                    elif(cmd == "LC_LQua"):
                        r = self.returnArrayLowerQuant(array)
                    elif(cmd == "LC_UQua"):
                        r = self.returnArrayHigherQuant(array)
                    elif(cmd == "DIV_SH"):
                        if len(classes) > 1:
                            r = self.f_returnShannonIndex(array,classes)
                        else:
                            r = None
                    elif(cmd == "DIV_SI"):
                        if len(classes) > 1:
                            r = self.f_returnSimpsonIndex(array,classes)
                        else:
                            r = None
                    elif(cmd == "DIV_EV"):
                        if len(classes) > 1:
                            r = self.f_returnShannonEqui(array,classes)
                        else:
                            r = None
                    # Get FieldValue of given Field
                    #id = self.getFieldValue(poly,landID)

                    id = poly.GetFID()
                    b = [id,cmd,r]
                    res.append(b)
            else:
                id = poly.GetFID()
                if self.featFailed.count(id) == 0:
                    self.featFailed.append(id)
                b = [id,cmd,None]
                res.append(b)
#             else:
#                 id = poly.GetFID()
#                 if self.featFailed.count(id) == 0:
#                     self.featFailed.append(id)
#                 b = [id,cmd,None]
#                 res.append(b)
            # Update the Statusbar of the current process
            if self.iface != None:
                self.iface.mainWindow().statusBar().showMessage("%s calculated for feature %s out of %s (%s impossible)" % (cmd, poly.GetFID()+1,self.lyr.GetFeatureCount(),len(self.featFailed) ))

        # Display number of errors in statusbar
        if self.error != 0:
            if self.iface != None:
                self.iface.mainWindow().statusBar().showMessage("%s could not be calculated for %s features" % (cmd,self.error ))

        return self.featFailed, res

    # Get value of a field name within a given feature of a ogr layer
    def getFieldValue(self,feat,name):
        i = feat.GetFieldIndex(str(name))
        id = feat.GetField(i)
        if id == None:
            id = feat.GetFID()
        return id

    # This function will convert the rasterized clipper shapefile
    # to a mask for use within GDAL.
    def imageToArray(self,i):
        """
        Converts a Python Imaging Library array to a
        gdalnumeric image.
        """
        try:
            a = numpy.fromstring(i.tostring(),'b')
        except AttributeError:
            try:
                a = numpy.fromstring(i.tobytes(),'b')   
            except SystemError:
                a = None
        if a != None:
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

    def Pixel2world(self,geoMatrix, x, y):
        ulX = geoMatrix[0]
        ulY = geoMatrix[3]
        xDist = geoMatrix[1]
        yDist = geoMatrix[5]
        coorX = (ulX + (x * xDist))
        coorY = (ulY + (y * yDist))
        return (coorX, coorY)

    # Returns an array from the given polygon feature
    # Assumes that the polygon is inside the rasters extent!
    def getClipArray(self,poly):
        # Convert the polygon extent to image pixel coordinates
        try:
            geom = poly.GetGeometryRef()
        except AttributeError:
            return None
        if geom.GetGeometryCount() > 1:
            # TODO: What to do with multipolygons?
            self.iface.messageBar().createMessage("LecoS - Warning","Your Shapefile contains Multipolygons which LecoS does not support")
            return None
        else:
            minX, maxX, minY, maxY = self.lyr.GetExtent() # geom.GetEnvelope()
            ulX, ulY = self.world2Pixel(self.geoTrans, minX, maxY)
            lrX, lrY = self.world2Pixel(self.geoTrans, maxX, minY)
            # Calculate the pixel size of the new image
            pxWidth = int(lrX - ulX)
            pxHeight = int(lrY - ulY)

            # If the clipping features extend out-of-bounds and ABOVE the raster...
            if self.geoTrans[3] < maxY:
                # In such a case... ulY ends up being negative--can't have that!
                iY = ulY
                ulY = 0

            # Clip the raster to the shapes boundingbox
            clip = self.srcArray[ulY:lrY, ulX:lrX]

            # Create a new geomatrix for the image that is covered by the layer
            geoTrans = list(self.geoTrans)
            geoTrans[0] = minX
            geoTrans[3] = maxY

            # Map points to pixels for drawing the boundary on a blank 8-bit, black and white, mask image.
            points = []
            pixels = []
            pts = geom.GetGeometryRef(0)

            for p in range(pts.GetPointCount()):
                points.append((pts.GetX(p), pts.GetY(p)))

            for p in points:
                pixels.append(self.world2Pixel(geoTrans, p[0], p[1])) # Transform nodes to geotrans of raster

            rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
            rasterize = ImageDraw.Draw(rasterPoly)
            rasterize.polygon(pixels, 0)

            # If the clipping features extend out-of-bounds and ABOVE the raster...
            if self.geoTrans[3] < maxY:
                # The clip features were "pushed down" to match the bounds of the
                #   raster; this step "pulls" them back up
                premask = self.imageToArray(rasterPoly)
                # We slice out the piece of our clip features that are "off the map"
                mask = numpy.ndarray((premask.shape[-2] - abs(iY), premask.shape[-1]), premask.dtype)
                mask[:] = premask[abs(iY):, :]
                mask.resize(premask.shape) # Then fill in from the bottom

                # Most importantly, push the clipped piece down
                geoTrans[3] = maxY - (maxY - self.geoTrans[3])
            else:
                mask = self.imageToArray(rasterPoly)

            # Do the actual clipping
            if mask != None:
                try:
                    clip2 = numpy.choose(mask,(clip, 0),mode='raise').astype(self.srcArray.dtype)
                except Exception:
                    self.error = self.error + 1
                    clip2 = None # Shape mismatch or Memory Error
                except ValueError:
                    # Cut the clipping features to the raster
                    rshp = list(mask.shape)
                    if mask.shape[-2] != clip2.shape[-2]:
                        rshp[0] = clip2.shape[-2]
                    if mask.shape[-1] != clip2.shape[-1]:
                        rshp[1] = clip2.shape[-1]
                    # Resize to the clip
                    mask.resize(*rshp, refcheck=False)

                    try:
                        clip2 = numpy.choose(mask,(clip,0),mode='raise').astype(self.srcArray.dtype)
                    except ValueError:
                        self.error = self.error + 1
                        clip2 = None # Shape mismatch or Memory Error
            else:
                self.error = self.error + 1
                clip2 = None # Image to array failed because polygon outside range
        return clip2

    # Bounding box intersection test
    def BBoxIntersect(self,rasE,polyE):
        #rasE = (6271.190835569453, 14271.195806587984, -94342.91093178833, -86548.67193043727)
        #polyE = (12271.143126975001, 14271.127244755786, -88280.72212288296, -86548.67193043727)
        # Get upper left point + height and width of both bbs
        b1_x = rasE[0]
        b1_y = rasE[2]
        b1_w = rasE[1] - rasE[0]
        b1_h = rasE[0] - rasE[2]

        b2_x = polyE[0]
        b2_y = polyE[2]
        b2_w = polyE[1] - polyE[0]
        b2_h = polyE[0] - polyE[2]

        # is b1 on the right side of b2? # is b1 under b2? # is b2 on the right side of b1? # is b2 under b1?
        if (b1_x > b2_x + b2_w- 1 ) or (b1_y > b2_y + b2_h - 1 ) or (b2_x > b1_x + b1_w - 1 ) or (b2_y > b1_y + b1_h - 1 ):
            # no collision
            return False
        else:
            # collision
            return True

    # Returns list of corner coordinates from a geotransform
    # Code from here http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
    def GetExtent(self,gt,cols,rows):
        ''' Return list of corner coordinates from a geotransform

            @type gt:   C{tuple/list}
            @param gt: geotransform
            @type cols:   C{int}
            @param cols: number of columns in the dataset
            @type rows:   C{int}
            @param rows: number of rows in the dataset
            @rtype:    C{[float,...,float]}
            @return:   coordinates of each corner
        '''
        ext=[]
        xarr=[0,cols]
        yarr=[0,rows]

        for px in xarr:
            for py in yarr:
                x=gt[0]+(px*gt[1])+(py*gt[2])
                y=gt[3]+(px*gt[4])+(py*gt[5])
                ext.append([x,y])
            yarr.reverse()
        return ext

    # Returns number of given cells
    def returnLCnumber(self,array,cl):
        return int(self.count_nonzero(array[array==cl]))

    # Returns the proportion of the labeled class in the landscape
    def returnLCproportion(self,array,cl):
        res = []
        classes = sorted(numpy.unique(array)) # get classes
        # Value 0 seems to be the default nodata-value
        for i in classes:
            arr = numpy.copy(array)
            arr[array!=i] = 0
            res.append(self.count_nonzero(arr))
        arr = numpy.copy(array)
        arr[array!=cl] = 0
        prop = self.count_nonzero(arr) / float(sum(res))
        return prop

    ## Unclassified Methods ##
    # Returns sum of clipped raster cells
    def returnArraySum(self,array):
        try:
            return numpy.sum(array[array!=self.nodata])
        except ValueError:
            return None

    # Returns mean of clipped raster cells
    def returnArrayMean(self,array):
        try:
            return numpy.mean(array[array!=self.nodata])
        except ValueError:
            return None

    # Returns standard deviation of clipped raster cells
    def returnArrayStd(self,array):
        try:
            return numpy.std(array[array!=self.nodata])
        except ValueError:
            return None

    # Returns the minimum of clipped raster cells
    def returnArrayMin(self,array):
        if numpy.size(array) != 0 and self.count_nonzero(array) != 0:
            try:
                return numpy.min(array[array!=self.nodata])
            except ValueError: # doesn't work always if no-data is a normal integer?
                return None
        else:
            return None

    # Returns the minimum of clipped raster cells
    def returnArrayMax(self,array):
        if numpy.size(array) != 0 and self.count_nonzero(array) != 0:
            try:
                return numpy.max(array[array!=self.nodata])
            except ValueError:
                return None
        else:
            return None

    # Returns the median of clipped raster cells
    def returnArrayMedi(self,array):
        if numpy.size(array) != 0 and self.count_nonzero(array) != 0:
            try:
                return numpy.median(array[array!=self.nodata])
            except ValueError:
                return None
        else:
            return None

    # Returns the weighed average of clipped raster cells
    def returnArrayLowerQuant(self,array):
        if numpy.size(array) != 0 and self.count_nonzero(array) != 0:
            try:
                return scipy.percentile(array[array!=self.nodata],25)
            except ValueError:
                return None
        else:
            return None

    # Returns the weighed average of clipped raster cells
    def returnArrayHigherQuant(self,array):
        if numpy.size(array) != 0 and self.count_nonzero(array) != 0:
            try:
                return scipy.percentile(array[array!=self.nodata],75)
            except ValueError:
                return None
        else:
            return None

    # Calculates the Shannon Index
    def f_returnShannonIndex(self,array,classes):
        sh = []
        cl_array = numpy.copy(array) # create working array
        cl_array[cl_array==int(self.nodata)] = 0
        for cl in classes:
            res = []
            for i in classes:
                arr = numpy.copy(array)
                arr[array!=i] = 0
                res.append(self.count_nonzero(arr))
            arr = numpy.copy(array)
            arr[array!=cl] = 0
            prop = self.count_nonzero(arr) / float(sum(res))
            sh.append(prop * math.log(prop))
        return sum(sh)*-1

    # Calculates the Simpson Index
    def f_returnSimpsonIndex(self,array,classes):
        si = []
        cl_array = numpy.copy(array) # create working array
        cl_array[cl_array==int(self.nodata)] = 0
        for cl in classes:
            res = []
            for i in classes:
                arr = numpy.copy(array)
                arr[array!=i] = 0
                res.append(self.count_nonzero(arr))
            arr = numpy.copy(array)
            arr[array!=cl] = 0
            prop = self.count_nonzero(arr) / float(sum(res))
            si.append(math.pow(prop,2))
        return 1-sum(si)
    # Calculates the Shannon Equitability / Eveness
    def f_returnShannonEqui(self,array,classes):
        return self.f_returnShannonIndex(array,classes) / math.log(len(classes))

##
# List all available landscape vector functions for use in the VectorBatchConverter class
def listVectorStatistics():
    functionList = []

    functionList.append(unicode("Class area")) # Calculate area of class
    functionList.append(unicode("Landscape Proportion")) # Landscape Proportion of class
    functionList.append(unicode("Number of Patches")) # Return Number of Patches
    functionList.append(unicode("Patch density")) # Return Patch density
    functionList.append(unicode("Mean patch area")) # Return Mean Patch area
    functionList.append(unicode("StDev patch area")) # Return Standard Deviation of Patch areas
    functionList.append(unicode("Median patch area")) # Return Median Patch area
    functionList.append(unicode("Greatest patch area")) # Return Greatest patch area
    functionList.append(unicode("Smallest patch area")) # Return Smallest patch area
    #functionList.append(unicode("Mean patch distance")) # Return Mean Patch distance
    # Edge Metrics
    functionList.append(unicode("Edge length")) # Calculate edge length
    functionList.append(unicode("Edge density")) # Calculate Edge Density
    functionList.append(unicode("Mean patch edge length")) # Calculate mean edge length of all patches
    # Shape Metric
    functionList.append(unicode("Mean patch shape ratio")) # Return Mean Patch shape
    #functionList.append(unicode("Overall Core area")) # Return Core area

    return functionList


# Landscape vector processing. Ether use a grouping field or an overlaying grid
# The calculation works by using SQL-queries
class VectorBatchConverter():
    def __init__(self,landscape,ID=None,classField=None,vectorPath=None,iface=None):
#         landPath = "/home/martin/Downloads/qgis_testing/land_use_clipped.shp"
#         ID = "Ponto"
#         datasource = ogr.Open(str(landPath))
#         layer = datasource.GetLayer(0)
#         layerName = layer.GetName()
#         d = datasource.ExecuteSQL("SELECT DISTINCT %s FROM %s" %(ID,layerName))
#         groups = []
#         for i in range(0,d.GetFeatureCount()):
#            f = d.GetFeature(i)
#            groups.append(f.GetField(0))
        landPath = landscape.source()
        self.ID = str( ID )
        self.datasource = ogr.Open(str(landPath))
        self.classField = str(classField)
        if self.datasource.GetLayerCount()!=1:
            func.DisplayError(self.iface,"LecoS: Warning" ,"Landscape Vector processing is currently only possible with ESRI shapefiles","WARNING")
            return
        else:
            self.layer = self.datasource.GetLayer(0) # Import layer 0 --> only works with shapefiles

        self.layerName = str( self.layer.GetName() )# Save the Layersname
        # Save the names of unique groups in an array
        d = self.datasource.ExecuteSQL("SELECT DISTINCT %s FROM %s" % (self.ID,self.layerName))
        self.groups = []
        for i in range(0,d.GetFeatureCount()):
            f = d.GetFeature(i)
            self.groups.append(f.GetField(0))

    # Runs a defined metric
    def go(self,name,cl=None):
        cl = str(cl)
        if(name == unicode("Class area")):# Calculate area of class
            return self.f_ClassArea(cl)
        if(name == unicode("Landscape Proportion")):# Landscape Proportion of class
            return self.f_LandscapeProportion(cl)
        if(name == unicode("Number of Patches")):# Return Number of Patches
            return self.f_NumberPatches(cl)
        if(name == unicode("Patch density")):# Return Patch density
            return self.f_PatchDensity(cl)
        if(name == unicode("Mean patch area")): # Return Mean Patch area
            return self.f_MeanPatchArea(cl)
        if(name == unicode("StDev patch area")): # Return Standard Deviation of Patch area
            return self.f_SDPatchArea(cl)
        if(name == unicode("Median patch area")): # Return Median Patch area
            return self.f_MedianPatchArea(cl)
        if(name == unicode("Greatest patch area")): # Return Greatest Patch area
            return self.f_MaxPatchArea(cl)
        if(name == unicode("Smallest patch area")): # Return Smallest Patch area
            return self.f_MinPatchArea(cl)
        # Edge Metrics
        if(name == unicode("Edge length")): # Calculates total edge length
            return self.f_EdgeLength(cl)
        if(name == unicode("Edge density")): # Calculate Edge Density
            return self.f_EdgeDensity(cl)
        if(name == unicode("Mean patch edge length")): # Calculate mean edge length of all patches
            return self.f_MeanEdgeLength(cl)
        # Shape Metric
        if(name == unicode("Mean patch shape ratio")): # Return Mean Patch shape
            return self.f_MeanShapeRatio(cl)
        # Zonal statistics and Diversity Indices
        if(name == unicode("LC_Sum")):
            return self.f_ClassArea(None,"LC_Sum")
        if(name == unicode("LC_Mean")):
            return self.f_MeanPatchArea(None,"LC_Mean")
        if(name == unicode("LC_SD")):
            return self.f_SDPatchArea(None,"LC_SD")
        if(name == unicode("LC_Med")):
            return self.f_MedianPatchArea(None,"LC_Med")
        if(name == unicode("LC_Max")):
            return self.f_MaxPatchArea(None,"LC_Max")
        if(name == unicode("LC_Min")):
            return self.f_MinPatchArea(None,"LC_Min")
        if(name == unicode("LC_LQua")):
            return self.f_MedianPatchArea(None,"LC_Med",25)
        if(name == unicode("LC_UQua")):
            return self.f_MedianPatchArea(None,"LC_Med",75)
        if(name == unicode("DIV_SH")):
            pass
            #return self.f_ShannonIndex()
        if(name == unicode("DIV_SI")):
            pass
        if(name == unicode("DIV_EV")):
            pass

    ## Metrics functions
    # Returns a list with the area of all features within a given group
    def returnGroupArea(self,group,cl=None):
        if cl == None:
            layers = self.datasource.ExecuteSQL("SELECT * FROM %s WHERE %s = '%s'" % (self.layerName, self.ID, group) )
        else:
            layers = self.datasource.ExecuteSQL("SELECT * FROM %s WHERE (%s = '%s') AND (%s = '%s')" % (self.layerName, self.ID, group,self.classField,cl) )
        res = []
        for i in range(0,layers.GetFeatureCount()):
            f = layers.GetFeature(i)
            g = f.GetGeometryRef()
            res.append(g.Area())
        return res

    # Returns a list with the perimeters of all features within a given group
    def returnGroupPerimeter(self,group,cl=None):
        if cl == None:
            layers = self.datasource.ExecuteSQL("SELECT * FROM %s WHERE %s = '%s'" % (self.layerName, self.ID, group) )
        else:
            layers = self.datasource.ExecuteSQL("SELECT * FROM %s WHERE (%s = '%s') AND (%s = '%s')" % (self.layerName, self.ID, group,self.classField,cl) )
        res = []
        for i in range(0,layers.GetFeatureCount()):
            f = layers.GetFeature(i)
            ref_geometry = f.GetGeometryRef()
            pts = ref_geometry.GetGeometryRef(0)
            points = []
            for p in xrange(pts.GetPointCount()):
                points.append((pts.GetX(p), pts.GetY(p)))
            Nedges = len(points)-1
            length = []
            for i in xrange(Nedges):
                ax, ay = points[i]
                bx, by = points[i+1]
                length.append(math.hypot(bx-ax, by-ay))
            res.append(numpy.sum(length))
        return res

    # Returns the number of all patches within a given group with optional class
    def returnGroupPatchNumber(self,group,cl=None):
        if cl == None:
            layers = self.datasource.ExecuteSQL("SELECT * FROM %s WHERE %s = '%s'" % (self.layerName, self.ID, group) )
        else:
            layers = self.datasource.ExecuteSQL("SELECT * FROM %s WHERE (%s = '%s') AND (%s = '%s')" % (self.layerName, self.ID, group,self.classField,cl) )

        return layers.GetFeatureCount()

    # Get mean patch area for each group and optionally class
    def f_MeanPatchArea(self,cl=None,name="Mean patch area"):
        res = []
        for group in self.groups:
            r = self.returnGroupArea(group,cl)
            try:
                v = numpy.mean(r)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get mean patch area for each group and optionally class
    def f_SDPatchArea(self,cl=None,name="StDev patch area"):
        res = []
        for group in self.groups:
            r = self.returnGroupArea(group,cl)
            try:
                v = numpy.std(r)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get median patch area for each group and optionally class
    def f_MedianPatchArea(self,cl=None,name="Median patch area",niv=50):
        res = []
        for group in self.groups:
            r = self.returnGroupArea(group,cl)
            try:
                v = scipy.percentile(r,niv)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get greatest patch area for each group and optionally class
    def f_MaxPatchArea(self,cl=None,name="Greatest patch area"):
        res = []
        for group in self.groups:
            r = self.returnGroupArea(group,cl)
            try:
                v = numpy.max(r)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get smallest patch area for each group and optionally class
    def f_MinPatchArea(self,cl=None,name="Smallest patch area"):
        res = []
        for group in self.groups:
            r = self.returnGroupArea(group,cl)
            try:
                v = numpy.min(r)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get patch density for each group and optionally class
    def f_PatchDensity(self,cl=None,name="Patch density"):
        res = []
        for group in self.groups:
            n = float(self.returnGroupPatchNumber(group,cl))
            r = self.returnGroupArea(group,None)
            try:
                v = numpy.sum(r)
                pd = (n / float(numpy.sum(r)))
            except ValueError: # Catch empty array
                pd = "NULL"
            res.append( [group,name,pd] )
        return res

    # Get total edge length of all patches each group and optionally class
    def f_EdgeLength(self,cl=None,name="Edge length"):
        res = []
        for group in self.groups:
            p = self.returnGroupPerimeter(group,cl)
            try:
                v = numpy.sum(p)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get Edge density for each group and optionally class
    def f_EdgeDensity(self,cl=None,name="Edge density"):
        res = []
        for group in self.groups:
            p = self.returnGroupPerimeter(group,cl)
            r = self.returnGroupArea(group,None)
            if len(p) == 0 or len(r) == 0:
                a = "NULL"
            else:
                a = (float(numpy.sum(p)) / float(numpy.sum(r)) )
            res.append( [group,name,a] )
        return res

    # Get Mean total edge length for all patches for each group and optionally class
    def f_MeanEdgeLength(self,cl=None,name="Mean patch edge length"):
        res = []
        for group in self.groups:
            p = self.returnGroupPerimeter(group,cl)
            try:
                v = numpy.mean(p)
            except ValueError: # Catch empty array
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get Number of patches for each group and optionally class
    def f_NumberPatches(self,cl=None,name="Number of Patches"):
        res = []
        for group in self.groups:
            n = self.returnGroupPatchNumber(group,cl)
            res.append( [group,name,n] )
        return res

    # Get Mean shape ratio (ratio perimeter/area) for all patches for each group and optionally class
    def f_MeanShapeRatio(self,cl=None,name="Mean patch shape ratio"):
        res = []
        for group in self.groups:
            a = self.returnGroupArea(group,cl)
            p = self.returnGroupPerimeter(group,cl)
            if len(a) == 0 or len(p) == 0:
                r = "NULL"
            else:
                r = numpy.divide(p,a)
                r = numpy.mean(r)
            res.append( [group,name,r] )
        return res

    # Get Patch area size for each group and class
    # CLASS METRIC ONLY
    def f_ClassArea(self,cl=None,name="Class area"):
        res = []
        for group in self.groups:
            a = self.returnGroupArea(group,cl)
            try:
                v = numpy.sum(a)
            except ValueError:
                v = "NULL"
            res.append( [group,name,v] )
        return res

    # Get Landscape proportion for each group and class
    # CLASS METRIC ONLY
    def f_LandscapeProportion(self,cl=None,name="Landscape Proportion"):
        res = []
        for group in self.groups:
            a = self.returnGroupArea(group)
            b = self.returnGroupArea(group,cl)
            if len(a) == 0 or len(b) == 0:
                prop = "NULL"
            else:
                prop = ( float(numpy.sum(b)) / float(numpy.sum(a)) )
            res.append( [group,name,prop] )
        return res
    ## Additional Landscape Metrics
    # Get Shannon Index for quantifying Landscape diversity
    # FIXME: Still to do
    def f_ShannonIndex(self,name="DIV_SH"):
        res = []
        for group in self.groups:
            a = self.returnGroupArea(group)
            numpy.sum(a) / float(sum(res))
            sh = []
            #  landscape wide / sum areas
            #  result * math.log(result)
            #  sum(res) * -1

    def f_SimpsonIndex(self,name="DIV_SI"):
        pass

    def f_EvenessIndex(self,name="DIV_EV"):
        pass
