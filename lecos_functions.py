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

import csv
from osgeo import ogr

# Save results to CSV
def saveToCSV( results, titles, filePath ):
  f = open(filePath, "wb" )
  writer = csv.writer(f,delimiter=';',quotechar="'",quoting=csv.QUOTE_ALL)
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
  
  lines.addWidget( QLabel( QApplication.translate( "LecoS", "<b>Citation:</b>") ) )
  cit = QLineEdit()
  cit.setText("Martin Jung, 2012, LecoS - A QGIS plugin to conduct landscape ecology statistics, http://plugins.qgis.org/plugins/LecoS/")
  lines.addWidget( cit )

  btnClose = QPushButton( QApplication.translate( "LecoS", "Close" ) )
  lines.addWidget( btnClose )
  QObject.connect( btnClose, SIGNAL( "clicked()" ), dlgAbout, SLOT( "close()" ) )

  dlgAbout.exec_()

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def lastUsedDir():
  settings = QSettings( "Lecoto", "lecos" )
  return settings.value( "lastUsedDir", QVariant( "" ) ).toString()

# Adapted from Plugin ZonalStats - Copyright (C) 2011 Alexander Bruy
def setLastUsedDir( lastDir ):
  path = QFileInfo( lastDir ).absolutePath()
  settings = QSettings( "Lecoto", "lecos" )
  settings.setValue( "lastUsedDir", QVariant( path ) )
  
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
  
# Add a new attribute to the vectorlayer
# Expected input: Array with [ID,Value]
def addAttributeToLayer(layer,cmd,results):
  # Open a Shapefile, and get field names
  provider = layer.dataProvider()
  allAttrs = provider.attributeIndexes()
  provider.select(allAttrs)
  caps = provider.capabilities()
  name = "ras_"+cmd
  # Create Attribute Coloumn
  ind = provider.fieldNameIndex(name)
  try:
    if ind == -1:
      if caps & QgsVectorDataProvider.AddAttributes:
        res = provider.addAttributes( [ QgsField(name,QVariant.Double) ] )
  except:
    return False
  ind = provider.fieldNameIndex(name)
  # Write values to newly created coloumn or to existing one
  try:
    for ar in results:
      if caps & QgsVectorDataProvider.ChangeAttributeValues:
        attrs = { ind : QVariant(round(ar[1],6)) }
        provider.changeAttributeValues({ ar[0] : attrs })
  except:
    return False
  layer.commitChanges()
  return True
    