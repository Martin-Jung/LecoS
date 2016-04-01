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
from qgis.utils import *
import qgis.utils
#from qgis.analysis import *
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect
import re # regular matching
import numpy
import scipy

# Try to import functions from osgeo
try:
    from osgeo import gdal
except ImportError:
    import gdal
try:
    from osgeo import ogr, osr
except ImportError:
    import ogr

# Register gdal and ogr drivers
if hasattr(gdal,"AllRegister"): # Can register drivers
    gdal.AllRegister() # register all gdal drivers
if hasattr(ogr,"RegisterAll"):
    ogr.RegisterAll() # register all ogr drivers

## CODE START ##
# Save results to CSV
def saveToCSV( results, titles, filePath ):
  f = open(filePath, "wb" )
  writer = csv.writer(f,delimiter=';',quotechar="",quoting=csv.QUOTE_NONE)
  writer.writerow(titles)
  for item in results:
    writer.writerow(item)
  f.close()

# Displays results in a table Dialog
def ShowResultTableDialog( metric_names, results ):
  dlg = QDialog()
  dlg.setWindowTitle( QApplication.translate( "Landcover statistics", "Landcover statistics", "Window title" ) )
  dlg.resize(700, 200)
  # Size Policy
  sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
  sizePolicy.setHorizontalStretch(0)
  sizePolicy.setVerticalStretch(0)
  sizePolicy.setHeightForWidth(dlg.sizePolicy().hasHeightForWidth())
  dlg.setSizePolicy(sizePolicy)

  lines = QVBoxLayout( dlg )

  rowCount = len(results)
  colCount = len(metric_names)
  tableWidget = QTableWidget()
  tableWidget.setRowCount(rowCount)
  tableWidget.setColumnCount(colCount)
  tableWidget.setHorizontalHeaderLabels(metric_names) # add header
  tableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
  tableWidget.resizeColumnsToContents()

  for id, item in enumerate(results):
    for place, value in enumerate(item):
      newItem = QTableWidgetItem(unicode(value))
      tableWidget.setItem(id,place,newItem)

  lines.addWidget(tableWidget)

  btnClose = QPushButton( QApplication.translate( "OK", "OK" ) )
  lines.addWidget( btnClose )
  QObject.connect( btnClose, SIGNAL( "clicked()" ), dlg, SLOT( "close()" ) )
  dlg.exec_()

# Version number 2 for nested metrics and features
def ShowResultTableDialog2( metric_names, results ):
  dlg = QDialog()
  dlg.setWindowTitle( QApplication.translate( "Landcover statistics", "Landcover statistics", "Window title" ) )
  dlg.resize(700, 700)
  # Size Policy
  sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
  sizePolicy.setHorizontalStretch(0)
  sizePolicy.setVerticalStretch(0)
  sizePolicy.setHeightForWidth(dlg.sizePolicy().hasHeightForWidth())
  dlg.setSizePolicy(sizePolicy)

  lines = QVBoxLayout( dlg )

  rowCount = len(results[0])
  colCount = len(metric_names)
  tableWidget = QTableWidget()
  tableWidget.setRowCount(rowCount)
  tableWidget.setColumnCount(colCount)
  tableWidget.setHorizontalHeaderLabels(metric_names) # add header
  tableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
  tableWidget.resizeColumnsToContents()

  for id, item in enumerate(results):
    for place, value in enumerate(item):
      idItem = QTableWidgetItem(unicode(value[0]))
      tableWidget.setItem(place,0,idItem)
      newItem = QTableWidgetItem(unicode(value[2]))
      tableWidget.setItem(place,id+1,newItem)

  lines.addWidget(tableWidget)

  btnClose = QPushButton( QApplication.translate( "OK", "OK" ) )
  lines.addWidget( btnClose )
  QObject.connect( btnClose, SIGNAL( "clicked()" ), dlg, SLOT( "close()" ) )
  dlg.exec_()
  return True


# Shows the about dialog
def AboutDlg( ):
  dlgAbout = QDialog()
  dlgAbout.setWindowTitle( QApplication.translate( "Landcover statistics", "About LecoS", "Window title" ) )
  lines = QVBoxLayout( dlgAbout )
  title = QLabel( QApplication.translate( "LecoS", "<b>LecoS</b>" ) )
  title.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
  lines.addWidget( title )
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "Contains analytical functions for landscape analysis" ) ) )
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "<b>Disclaimer:</b>" ) ) )
  text = "This piece of software comes as it is.<br> The developer takes no responsiblity for any miscalcultions or errors in the code.<br> Users are encouraged to use their brain to validate any returned results."
  lines.addWidget( QLabel( text ) )
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "<b>Developer:</b>" ) ) )
  lines.addWidget( QLabel( "Martin Jung" ) )
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "<b>Homepage:</b>") ) )

  link = QLabel( "<a href=\"http://conservationecology.wordpress.com\">http://conservationecology.wordpress.com</a>" )

  link.setOpenExternalLinks( True )
  lines.addWidget( link )
  # Citation
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "<b>Citation:</b>") ) )
  cit = QLineEdit()
  cit.setText("Martin Jung (2016) LecoS - A python plugin for automated landscape ecology analysis, Ecological Informatics, 31, 18-21 http://dx.doi.org/10.1016/j.ecoinf.2015.11.006")
  lines.addWidget( cit )
  # Supported by
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "<b>Supported by:</b>") ) )
  sup = QLabel( QApplication.translate( "LecoS", "<p>Universidade de &#201;vora, Departamento de Biologia, Unidade de Biologia da Conserva&#231;&#479;o</p>" ) )
  sup.setWordWrap(True)
  lines.addWidget( sup )
  Pic = QLabel()
  Pic.setPixmap(QPixmap(":/pics/icons/evora_small.jpg"))
  lines.addWidget(Pic)

  btnClose = QPushButton( QApplication.translate( "LecoS", "Close" ) )
  lines.addWidget( btnClose )
  QObject.connect( btnClose, SIGNAL( "clicked()" ), dlgAbout, SLOT( "close()" ) )

  dlgAbout.exec_()

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def lastUsedDir():
  settings = QSettings( "Lecoto", "lecos" )
  return settings.value( "lastUsedDir", str( "" ) )

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def setLastUsedDir( lastDir ):
  path = QFileInfo( lastDir ).absolutePath()
  settings = QSettings( "Lecoto", "lecos" )
  settings.setValue( "lastUsedDir", str( path ) )

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def getRasterLayerByName( layerName ):
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.RasterLayer and ( layer.providerType() == 'gdal' ) and layer.name() == layerName:
        if layer.isValid():
          return layer
        else:
          return None

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def getRasterLayersNames():
  layerList = []
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.RasterLayer and ( layer.providerType() == 'gdal' ):
        layerList.append( unicode( layer.name() ) )
  return layerList

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def getVectorLayerByName( layerName ):
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
      if layer.isValid():
        return layer
      else:
        return None

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def getVectorLayersNames():
  layerList = []
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon:
      layerList.append( unicode( layer.name() ) )
  return layerList

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def getFieldList( vLayer ):
  vProvider = vLayer.dataProvider()
  return vProvider.fields()

# Get all field values of a given attribute from a vector layer
def getAttributeList( vlayer, field):
  path = vlayer.source()
  datasource = ogr.Open(str(path))
  layer = datasource.GetLayer(0)
  layerName = layer.GetName()
  field = str(field)
  try:
    d = datasource.ExecuteSQL("SELECT %s FROM %s" % (field,layerName))
  except RuntimeError:
    QMessageBox.warning(QDialog(),"LecoS: Warning","Failed to query the vector layers attribute table")
    return
  attr = []
  for i in range(0,d.GetFeatureCount()):
    f = d.GetFeature(i)
    attr.append(f.GetField(0))
  return attr

# General function to retrieve layers
def getLayerByName( layerName ):
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.name() == layerName:
        if layer.isValid():
          return layer
        else:
          return None

# Save multiple different attributes to vector table
# Input = [[[ID,METRIC,VAL],[ID,METRIC,VAL]],[[ID,METRIC,VAL2],[ID,METRIC,VAL2]]]
def addAttributesToLayer(layer,results):
  # Open a Shapefile, and get field names
  provider = layer.dataProvider()
  caps = provider.capabilities()

  for metric in xrange(0,len(results)):
    # Create Attribute Column
    # Name Formating
    cmd = str( results[metric][0][1] )
    cmd = string.capwords(cmd)
    cmd = string.split(cmd)
    name = ""
    for i in range(0,len(cmd)):
      if len(cmd) == 1:
        name = name + cmd[i]
      else:
        name = name + cmd[i][0:3]
    name = name[0:9] # Make sure only 10 character are Inside the Name
    ind = provider.fieldNameIndex(name)
    try:
      if ind == -1: # Already existing?
        if caps & QgsVectorDataProvider.AddAttributes:
          res = provider.addAttributes( [ QgsField(name,QVariant.Double) ] )
          if res == False:
            return res
    except:
      return False
    ind = provider.fieldNameIndex(name) # Check again if attribute is existing
    if ind != -1:
      # Write values to newly created coloumn or to existing one
      for ar in results[metric]:
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
          try:
            attrs = { ind : (round(ar[2],6)) }
          except:
            attrs = { ind : (ar[2]) }
          provider.changeAttributeValues({ ar[0] : attrs })
        else:
          return False
    else:
      return False

  layer.commitChanges()
  return True



# Save a rasterfile as geotiff to a given directory
# Need the previous raster (for output size and projection)
# and a path with writing permissions
def exportRaster(array,rasterSource,path,nodata=True):
  raster = gdal.Open(str(rasterSource))
  rows = raster.RasterYSize
  cols = raster.RasterXSize
  if nodata == True:
    nodata = raster.GetRasterBand(1).GetNoDataValue()
  elif nodata == False:
    nodata = 0
  else: # take nodata as it comes
    nodata = nodata

  driver = gdal.GetDriverByName('GTiff')
  # Create File based in path
  try:
    outDs = driver.Create(path, cols, rows, 1, gdal.GDT_Float32)
  except RuntimeError:
    QMessageBox.warning(QDialog(),"Could not overwrite file. Check permissions!")
    return
  if outDs is None:
    QMessageBox.warning(QDialog(),"Could not create output File. Check permissions!")
    return

  band = outDs.GetRasterBand(1)
  band.WriteArray(array)

  # flush data to disk, set the NoData value
  band.FlushCache()
  try:
    band.SetNoDataValue(nodata)
  except TypeError:
    band.SetNoDataValue(-9999) # set -9999 in the meantime

  # georeference the image and set the projection
  outDs.SetGeoTransform(raster.GetGeoTransform())
  outDs.SetProjection(raster.GetProjection())

  band = outDs = None # Close writing

# Adds a generated Raster to the QGis table of contents
def rasterInQgis(rasterPath):
  fileName = str(rasterPath)
  fileInfo = QFileInfo(fileName)
  baseName = fileInfo.baseName()
  rlayer = QgsRasterLayer(fileName, baseName)
  if not rlayer.isValid():
    QMessageBox.warning(QDialog(),"Failed to add the generated Layer to QGis")

  QgsMapLayerRegistry.instance().addMapLayer(rlayer)

# Adds a vector layer to the QGis table of contents
def tableInQgis(vectorPath):
  fileName = str(vectorPath)
  fileInfo = QFileInfo(fileName)
  baseName = fileInfo.baseName()
  uri = "file:/"+fileName+"?delimiter=%s" % (";")
  vlayer = QgsVectorLayer(uri, baseName, "delimitedtext")
  if not vlayer.isValid():
    QMessageBox.warning(QDialog(),"LecoS: Warning","Failed to add the Layer to QGis")
  QgsMapLayerRegistry.instance().addMapLayer(vlayer)

# Error messages wrapper
def DisplayError(iface,header,text,type="WARNING",time=4,both=False):
  if QGis.QGIS_VERSION_INT >= 10900:
    # What time of message?
    if type=="INFO":
      ob = QgsMessageBar.INFO
    elif type=="WARNING":
      ob = QgsMessageBar.WARNING
    elif type=="CRITICAL":
      ob = QgsMessageBar.CRITICAL

    # Show the Message Bar
    iface.messageBar().pushMessage(header,text, ob, time)
    if both: # Should the Messagebox also be shown?
      if type == "WARNING":
        QMessageBox.warning( QDialog(), header, text )
      elif type=="INFO":
        QMessageBox.information( QDialog(), header, text )
      elif type=="CRITICAL":
        QMessageBox.critical( QDialog(), header, text )
  else:
    if type == "WARNING":
      QMessageBox.warning( QDialog(), header, text )
    elif type=="INFO":
      QMessageBox.information( QDialog(), header, text )
    elif type=="CRITICAL":
      QMessageBox.critical( QDialog(), header, text )

# Create basic raster without projection
def createRaster(output,cols,rows,array,nodata,gt,d='GTiff'):

    driver = gdal.GetDriverByName(d)
    # Create File based in path
    try:
        tDs = driver.Create(output, cols, rows, 1, gdal.GDT_Float32)
    except RuntimeError:
        raise GeoAlgorithmExecutionException("Could not generate output file.")

    try:
        band = tDs.GetRasterBand(1)
    except AttributeError:
        raise GeoAlgorithmExecutionException("Please load a projected file first!")
    band.WriteArray(array)

    # flush data to disk, set the NoData value
    band.FlushCache()
    try:
      band.SetNoDataValue(nodata)
    except TypeError:
      band.SetNoDataValue(-9999) # set -9999 in the meantime

    # georeference the image and set the projection
    tDs.SetGeoTransform(gt)

    # Then set projection of current active layer
    epsg = qgis.utils.iface.activeLayer().crs().authid() #mapCanvas().mapRenderer().destinationCrs().srsid()
    coord_system = osr.SpatialReference()    
    coord_system.ImportFromEPSG( int(re.findall('\d+', epsg)[0]) )
    tDs.SetProjection(coord_system.ExportToWkt())

    band = tDs = None # Close writing

# Alternative count_nonzero function from scipy if available
def count_nonzero(array):
    if hasattr(numpy,'count_nonzero'):
        return numpy.count_nonzero(array)
    elif hasattr(scipy,'count_nonzero'):
        return scipy.count_nonzero(array)
    else:
        return (array != 0).sum()

