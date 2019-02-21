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

from qgis.PyQt.QtCore import ***************************************************
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
from builtins import object
from PyQt5.QtWidgets import QAction
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

# Import QGIS analysis tools
from qgis.core import QgsApplication
from .lecos_sextanteprov import LecoSAlgorithmsProv
#from qgis.analysis import *
# Import base libraries
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect
# Initialize Qt resources from file resources_rc.py
from .ui import resources_rc
# Import the code for the dialogs
from .lecos_dlg import LecosDialog
# Import Batch Dialog
from .lecos_dlg import BatchDialog
# Import RasterModifier Dialog
from .lecos_dlg import LandMod
# Import functions for about Dialog
from . import lecos_functions as func

## CODE START ##
class LecoS( object ):
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/python/plugins/LecoS"
        self.provider = LecoSAlgorithmsProv()

    def initGui(self):
        # Create action that will start the LecoS Plugin
        self.actionLecoS = QAction(QIcon(self.plugin_dir+"/icons/icon.png"),\
            u"Landscape statistics", self.iface.mainWindow())
        self.actionLecoS.triggered.connect(self.run)
        QgsApplication.processingRegistry().addProvider(self.provider)
        
        # Create action for small batch dialog
        self.actionBatch = QAction(QIcon(self.plugin_dir+"/icons/icon_batchCover.png"),\
            u"Landscape vector overlay", self.iface.mainWindow())
        self.actionBatch.triggered.connect(self.runBatch)
        
        # Create action for small RasterModifier dialog
        self.actionLMod = QAction(QIcon(self.plugin_dir+"/icons/icon_LandMod.png"),\
            u"Landscape modifications", self.iface.mainWindow())
        self.actionLMod.triggered.connect(self.runLMod)

        # check if Raster menu available
        if hasattr(self.iface, "addPluginToRasterMenu"):
            self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionLecoS)
            self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionBatch)
            self.iface.addPluginToRasterMenu("&Landscape Ecology", self.actionLMod)
        else:
            # no menu, place plugin under Plugins menu and toolbox as usual
            self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionLecoS)
            self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionBatch)
            self.iface.addPluginToMenu(u"&Landscape Ecology", self.actionLMod)
        
    def unload(self):
        # check if Raster menu available and remove our buttons from appropriate
        if hasattr(self.iface, "addPluginToRasterMenu"):
            self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionLecoS)
            self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionBatch)
            self.iface.removePluginRasterMenu("&Landscape Ecology",self.actionLMod)   
        else:
            # Remove the plugin menu item and icon
            self.iface.removePluginMenu(u"&Landscape Ecology",self.actionLecoS)
            self.iface.removePluginMenu(u"&Landscape Ecology",self.actionBatch)
            self.iface.removePluginMenu(u"&Landscape Ecology",self.actionLMod)    
        QgsApplication.processingRegistry().removeProvider(self.provider)
        
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
        #dlg.overrideWindowFlags(Qt.WA_DeleteOnClose)
        result = dlg.exec_()
        
    # Executes small LandscapeMod gui
    def runLMod(self):
        dlg = LandMod( self.iface )
        dlg.show()
        result = dlg.exec_()
    