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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources_rc.py
from ui import resources_rc
# Import the code for the dialogs
from lecos_dlg import LecosDialog
# Import small Div Dialog
from lecos_dlg import DivDialog
# Import Batch Dialog
from lecos_dlg import BatchDialog
# Import RasterIndexer Dialog
from lecos_dlg import RasterIndDialog

# Import functions for about Dialog
import lecos_functions as func

class LecoS( object ):
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/LecoS"

    def initGui(self):
        # Create action that will start the LecoS Plugin
        self.actionLecoS = QAction(QIcon(self.plugin_dir+"/icons/icon.png"),\
            u"Land cover statistics", self.iface.mainWindow())
        QObject.connect(self.actionLecoS, SIGNAL("triggered()"), self.run)
        
        # Create action for small batch dialog
        self.actionBatch = QAction(QIcon(self.plugin_dir+"/icons/icon_batchCover.png"),\
            u"Land cover polygon overlay", self.iface.mainWindow())
        QObject.connect(self.actionBatch, SIGNAL("triggered()"), self.runBatch)
                
        # Create action for small diversity dialog
        self.actionDivDlg = QAction(QIcon(self.plugin_dir+"/icons/icon_diversity.png"),\
            u"Diversity indices for Raster", self.iface.mainWindow())
        QObject.connect(self.actionDivDlg, SIGNAL("triggered()"), self.runDiv)
        
        # Create action for small RasterIndexer dialog
        self.actionRastInd = QAction(QIcon(self.plugin_dir+"/icons/icon_diversity.png"),\
            u"Create Fragmentation Index Map", self.iface.mainWindow())
        QObject.connect(self.actionRastInd, SIGNAL("triggered()"), self.runRasI)

        # check if Raster menu available
        if hasattr(self.iface, "addPluginToRasterMenu"):
            # Raster menu and toolbar available
            self.iface.addRasterToolBarIcon(self.actionLecoS)
            self.iface.addRasterToolBarIcon(self.actionBatch)
            self.iface.addRasterToolBarIcon(self.actionDivDlg)
            self.iface.addRasterToolBarIcon(self.actionRastInd)
            self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionLecoS)
            self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionBatch)
            self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionDivDlg)
            #self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionRastInd)
        else:
            # no menu, place plugin under Plugins menu and toolbox as usual
            self.iface.addToolBarIcon(self.actionLecoS)
            self.iface.addToolBarIcon(self.actionBatch)
            self.iface.addToolBarIcon(self.actionDivDlg)
            self.iface.addToolBarIcon(self.actionRastInd)
            self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionLecoS)
            self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionBatch)
            self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionDivDlg)
            #self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionRastInd)

    
    def unload(self):
        # check if Raster menu available and remove our buttons from appropriate
        if hasattr(self.iface, "addPluginToRasterMenu"):
            self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionLecoS)
            self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionBatch)
            self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionDivDlg)
            #self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionRastInd)            
            self.iface.removeRasterToolBarIcon(self.actionLecoS)
            self.iface.removeRasterToolBarIcon(self.actionBatch)
            self.iface.removeRasterToolBarIcon(self.actionDivDlg)
            #self.iface.removeRasterToolBarIcon(self.actionRastInd)
        else:
            # Remove the plugin menu item and icon
            self.iface.removePluginMenu(u"&Landscape Ecology",self.actionLecoS)
            self.iface.removePluginMenu(u"&Landscape Ecology",self.actionBatch)
            self.iface.removePluginMenu(u"&Landscape Ecology",self.actionDivDlg)
            #self.iface.removePluginMenu(u"&Landscape Ecology",self.actionRastInd)            
            self.iface.removeToolBarIcon(self.actionLecoS)
            self.iface.removeToolBarIcon(self.actionBatch)
            self.iface.removeToolBarIcon(self.actionDivDlg)
            #self.iface.removeToolBarIcon(self.actionRastInd)

    # run method that performs all the real work
    def run(self):
        # create and show the dialog
        dlg = LecosDialog( self.iface )
        # show the dialog
        dlg.show()
        result = dlg.exec_()
    
    # Executes small Diversity gui
    def runBatch(self):
        dlg = BatchDialog( self.iface )
        dlg.show()
        result = dlg.exec_()
        
    # Executes small Diversity gui
    def runDiv(self):
        dlg = DivDialog( self.iface )
        dlg.show()
        result = dlg.exec_()
    
    # Executes small RasterIndex gui
    def runRasI(self):
        dlg = RasterIndDialog( self.iface )
        dlg.show()
        result = dlg.exec_()
    
