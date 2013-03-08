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
from qgis.analysis import *

# import Ui
from ui.dlg_landscapestatistics import Ui_Lecos
from ui.dlg_PolygonPerLandCover import Ui_BatchDialog
from ui.dlg_DiversityDialog import Ui_DivDialog
from ui.dlg_LandscapeModifier import Ui_LandMod

# Import functions and metrics
import lecos_functions as func
import landscape_statistics as lcs
import landscape_diversity as ldiv
import landscape_polygonoverlay as pov 
import landscape_modifier as lmod

# Dependencies
import numpy, scipy, gdal, ogr
import subprocess              
from os import path
import tempfile
tmpdir = tempfile.gettempdir()


# create the dialog controls and set up the user interface from Designer.
class LecosDialog(QDialog, Ui_Lecos):
    def __init__(self, iface):
        # Initialize the Dialog
        QDialog.__init__( self )
        self.setupUi(self)
        self.iface = iface
        
        # Get and set current pixelsize
        if self.cbRaster.currentIndex() == -1:
            self.sp_cellsize.setEnabled( False )
            self.NoDataVal.setEnabled( False )
        else:
            self.sp_cellsize.setEnabled( True )
            self.NoDataVal.setEnabled( True )
            self.NoDataVal.setToolTip(QString(str("Please note that the nodata value must be an integer")))
            self.cellSizer( self.cbRaster.currentText() )
            self.setNoData( self.cbRaster.currentText() )
        
        #Change on Rasterfile
        QObject.connect( self.cbRaster, SIGNAL( "currentIndexChanged( QString )" ), self.cellSizer)
        QObject.connect( self.cbRaster, SIGNAL( "currentIndexChanged( QString )" ), self.setNoData)
                        
        # Save File
        QObject.connect( self.where2Save, SIGNAL( "clicked()" ), self.selectSaveFile )
        QObject.connect( self.rbDirect, SIGNAL( "clicked()" ), self.savetoggle )
        QObject.connect( self.rbSAVE, SIGNAL( "clicked()" ), self.savetoggle )


        # Change on Metric-Tabs
        QObject.connect( self.SingleMetric, SIGNAL( "currentIndexChanged( QString )" ), self.showFunctionHelp)
        QObject.connect( self.btn_right, SIGNAL( "clicked()" ), self.switchR )
        QObject.connect( self.btn_left, SIGNAL( "clicked()" ), self.switchL )
        QObject.connect( self.SelectAll, SIGNAL( "stateChanged( int )" ), self.SelectAllInListL )
        QObject.connect( self.SelectAll_2, SIGNAL( "stateChanged( int )" ), self.SelectAllInListR )

        # Button box 
        QObject.connect( self.btn_About, SIGNAL( "clicked()" ), self.showAbout )
        self.AcceptButton = self.bt_Accept.button( QDialogButtonBox.Ok )
        self.closeButton = self.bt_Accept.button( QDialogButtonBox.Cancel )
        
        # Manage current Raster-Layers
        self.Startup()
    
    # Shows the help for a single function
    def showFunctionHelp( self, name ):
        text = lcs.returnHelp(name,self.SingleMetricHelp)

    # Sets the nodata value inside the field
    def setNoData( self, rasterName ):
        if rasterName != -1:
            raster = func.getRasterLayerByName( self.cbRaster.currentText() )
            rasterPath = raster.source()
            raster = gdal.Open(str(rasterPath))
            band = raster.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            self.NoDataVal.setEnabled( True )
            try:
                self.NoDataVal.setValidator(QDoubleValidator(-999999,999999,5))
            except TypeError: # Trying to catch up some strange Errors with this QT-Validator
                self.NoDataVal.setValidator(QDoubleValidator(-999999,999999,5,self))
                if isinstance(nodata,int)==False:
                    QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                           self.tr( "Please format your rasters no-data value to integer (-99999 <-> 99999)" ) )
                
            self.NoDataVal.setText( QString(str(nodata)) ) 
            
    # Update Cellsize if a valid raster-file is selected
    def cellSizer( self, rasterName ):
        if rasterName != -1:
            pixelSize = func.getRasterLayerByName( rasterName ).rasterUnitsPerPixel()
            self.sp_cellsize.setEnabled( True )
            self.sp_cellsize.setValue( pixelSize )        
    
    # Save radio button
    def savetoggle( self ):
        if self.rbDirect.isChecked():
            self.SaveCsv.setEnabled( False )
            self.where2Save.setEnabled( False )
        elif self.rbSAVE.isChecked():
            self.SaveCsv.setEnabled( True )
            self.where2Save.setEnabled( True )
        
    # Where to save the csv
    def selectSaveFile( self ):   
        lastUsedDir = func.lastUsedDir()
        fileName = QFileDialog.getSaveFileName( self, self.tr( "Save data as" ),\
        lastUsedDir, "CSV files (*.csv *.CSV)" )
        if fileName.isEmpty():
            return
        func.setLastUsedDir( fileName )
        # ensure the user never ommited the extension from the file name
        if not fileName.toLower().endsWith( ".csv" ):
            fileName += ".csv"
        self.SaveCsv.setText( fileName )
        self.SaveCsv.setEnabled( True ) 
        
    # Manage Layout and startup parameters
    def Startup( self ):
        # Unable unused fields
        self.SaveCsv.setEnabled( False )
        self.where2Save.setEnabled( False )
        self.SingleMetricHelp.setEnabled( False )
        
        # Load in raster files
        self.cbRaster.addItems( func.getRasterLayersNames() )
        
        # Display functions
        self.SingleMetric.addItems( lcs.listStatistics() )
        self.showFunctionHelp( self.SingleMetric.currentText() )
        self.list_left.addItems( lcs.listStatistics() )
        self.rlistCounter.setText( str(self.list_left.count()) )
        self.rlistCounter_2.setText( str(self.list_right.count()) )
        
        self.MetricTab.setCurrentIndex( 0 ) # Startup on single metric tab
        self.MetricTab.setTabEnabled(2,False) # Disable Custom Tab
        
    # Switch Items on the several Metric Tab to the Right
    def switchR( self ):
        items = self.list_left.selectedItems()
        for item in items:
            n = self.list_left.row(item)    # get the index/row of the item
            i = self.list_left.takeItem(n)  # pop
            self.list_right.addItem(i)      # add to right QListWidget
            self.list_left.removeItemWidget( item ) # remove from left QListWidget
            #update counter
        self.rlistCounter.setText( str(self.list_left.count()) )
        self.rlistCounter_2.setText( str(self.list_right.count()) )
                
    # Switch Items on the several Metric Tab to the Left
    def switchL( self ):
        items = self.list_right.selectedItems()
        for item in items:
            n = self.list_right.row(item)    # get the index/row of the item
            i = self.list_right.takeItem(n)  # pop
            self.list_left.addItem(i)      # add to left QListWidget
            self.list_right.removeItemWidget( item ) # remove from right QListWidget
            #update counter
        self.rlistCounter.setText( str(self.list_left.count()) )
        self.rlistCounter_2.setText( str(self.list_right.count()) )

    # Select all Items in left List
    def SelectAllInListL ( self, state ):
        if state == Qt.Checked:
            allitems = self.list_left.findItems("*", Qt.MatchWrap | Qt.MatchWildcard)
            for item in allitems:
                item.setSelected( True )
        elif state == Qt.Unchecked:
            self.list_left.clearSelection()
                    
    # Select all Items in right List
    def SelectAllInListR ( self, state ):
        if state == Qt.Checked:
            allitems = self.list_right.findItems("*", Qt.MatchWrap | Qt.MatchWildcard)
            for item in allitems:
                item.setSelected( True )        
        elif state == Qt.Unchecked:
            self.list_right.clearSelection()
    
    # Show About Dialog
    def showAbout( self ):
        func.AboutDlg()
    
    # Accept current selection and metric
    def accept( self ):
        # check minimal input parameters
        if self.cbRaster.currentIndex() == -1:
            QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                           self.tr( "Please load a classified landcover layer into QGis first" ) )
            return
        if self.rbSAVE.isChecked():
            if self.SaveCsv.text().isEmpty():
                QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                            self.tr( "Please select where to save the results" ) )
                return
            if path.exists(self.SaveCsv.text()):
                QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                            self.tr( "File already exisits. Please select another path or delete file" ) )
                return
        if self.sp_cellsize.value() == 0:
            QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                           self.tr( "Please entry a correct cellsize (greater zero)" ) )
            return
        
        # Values and Preset
        self.progressBar.setRange( 0, 4)
        self.progressBar.setValue( 0 ) # pb start
        
        raster = func.getRasterLayerByName( self.cbRaster.currentText() )
        rasterPath = raster.source()
        dataPath = self.SaveCsv.text()
        cellsize = self.sp_cellsize.value()
        nodata = float(self.NoDataVal.text())
        
        ## Calculate Single Metric
        what = self.MetricTab.currentIndex()
        # Single
        if(what == 0):
            if len(self.SingleMetric.currentText()) >= 5:
                classes, array = lcs.f_landcover(rasterPath,nodata)
                self.progressBar.setValue( self.progressBar.value() + 1 )
                # Looping through all classes
                res = []
                res_tit = ["Class"]
                cl_analys = lcs.LandCoverAnalysis(array,cellsize,classes)
                for cl in classes:
                    cl_array = numpy.copy(array) # new working array
                    cl_array[cl_array!=cl] = 0
                    cl_analys.f_ccl(cl_array) # CC-labeling
                    name, result = cl_analys.execSingleMetric(self.SingleMetric.currentText(),cl) # Returns values for all 
                    
                    self.progressBar.setValue( self.progressBar.value() + 1 )
                    # Append Values to result class and table name array
                    r = [cl, result]
                    if len(res) == 0:
                        res.append(r)
                    else:
                        no_class_in_array = True
                        for id, item in enumerate(res):
                            if item[0] == cl:
                                res[id].append(result)
                                no_class_in_array = False
                        if no_class_in_array:
                            res.append(r)
                            
                    if res_tit.count(name) == 0:
                        res_tit.append(name)
            else:
                QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                           self.tr( "Please select a valid single metric" ) )

        ## Several Metrics
        elif(what == 1):
            metrics = []
            allitems = self.list_right.findItems("*", Qt.MatchWrap | Qt.MatchWildcard)
            if len(allitems)==0:
                QMessageBox.warning( self, self.tr( "LecoS: Warning" ), self.tr( "Please select at least one item from the left list" ) )
                return
            for item in allitems:
                metrics.append(unicode(item.text()))
            classes, array = lcs.f_landcover(rasterPath,nodata)
            self.progressBar.setValue( self.progressBar.value() + 1 )
            # Looping through all classes
            res = []
            res_tit = ["Class"]
            cl_analys = lcs.LandCoverAnalysis(array,cellsize,classes)
            for m in metrics:
                for cl in classes:
                    cl_array = numpy.copy(array) # new working array
                    cl_array[cl_array!=cl] = 0
                    cl_analys.f_ccl(cl_array) # CC-Labeling
                    name, result = cl_analys.execSingleMetric(m,cl)
                        
                    self.progressBar.setValue( self.progressBar.value() + 1 )
                    # Append Values to result class and table name array
                    r = [cl, result]
                    if len(res) == 0:
                        res.append(r)
                    else:
                        no_class_in_array = True
                        for id, item in enumerate(res):
                            if item[0] == cl:
                                res[id].append(result)
                                no_class_in_array = False
                        if no_class_in_array:
                            res.append(r)
                            
                    if res_tit.count(name) == 0:
                        res_tit.append(name)
        self.progressBar.setValue( self.progressBar.value() + 1 )
        # Write results
        if self.rbSAVE.isChecked():
            func.saveToCSV(res,res_tit,dataPath)
        else:
            func.ShowResultTableDialog(res_tit, res)
        self.progressBar.setValue( self.progressBar.value() + 1 )
        self.close()

# Gui for displaying certain diversity indices
class DivDialog(QDialog, Ui_DivDialog):
    def __init__(self, iface):
        # Initialize the Dialog
        QDialog.__init__( self )
        self.setupUi(self)
        self.iface = iface
        
        # Add Diversity Indices
        self.div = ["Shannon Index","Simpson Index", "Eveness"]
        self.cbDivselect.addItems( self.div )
        
        # Configure Connectors
        self.AcceptButton = self.btn_ok.button( QDialogButtonBox.Ok )
        self.closeButton = self.btn_ok.button( QDialogButtonBox.Cancel )
        QObject.connect( self.AcceptButton, SIGNAL( "clicked()" ), self.go )
        
        self.startup()
    
    # Configure GUI
    def startup(self):
        # Load in raster files
        self.cbRaster.addItems( func.getRasterLayersNames() )
    
    # Calculates Diversity indices    
    def go(self):
        if self.cbRaster.currentIndex() == -1:
            QMessageBox.warning( self, self.tr( "DivDialog: Warning" ),
                           self.tr( "Please load and select a classified raster first" ) )
            return
        raster = func.getRasterLayerByName( self.cbRaster.currentText() )
        rasterPath = raster.source()
        seldiv = unicode( self.cbDivselect.currentText() )
        
        div_cl = ldiv.LandscapeDiversity(rasterPath)
        if seldiv == "Shannon Index":
            r = div_cl.f_returnDiversity("shannon")
        elif seldiv == "Simpson Index":
            r = div_cl.f_returnDiversity("simpson")
        elif seldiv == "Eveness":
            r = div_cl.f_returnDiversity("eveness")
        
        self.output(r,seldiv)
    
    # Creates a small output dialog
    def output(self, result, index):
        dlg = QDialog()
        dlg.setWindowTitle( QApplication.translate( "Diversity Results", "Results", "Window title" ) )
        lines = QVBoxLayout( dlg )
        lab = QLabel( QApplication.translate( "Diversity Results", "<b>Results for "+index+":</b>" ) )
        lines.addWidget( lab )
        res = QLineEdit()
        res.setText(str(result))
        lines.addWidget( res )

        btnClose = QPushButton( QApplication.translate( "Diversity Results", "Close" ) )
        lines.addWidget( btnClose )
        QObject.connect( btnClose, SIGNAL( "clicked()" ), dlg, SLOT( "close()" ) )

        dlg.exec_()

# Gui for batch computing Landcover for vector features
class BatchDialog(QDialog, Ui_BatchDialog):
    def __init__(self, iface):

        # Initialize the Dialog
        QDialog.__init__( self )
        self.setupUi(self)
        self.iface = iface
        
        # Connects
        QObject.connect( self.cb_Vector, SIGNAL( "currentIndexChanged( QString )" ), self.featureCount)
        QObject.connect( self.cb_Classified, SIGNAL( "currentIndexChanged( QString )" ), self.EnableStuff)

        # Button box 
        self.AcceptButton = self.startButtons.button( QDialogButtonBox.Ok )
        QObject.connect( self.AcceptButton, SIGNAL( "clicked()" ), self.go )
        self.closeButton = self.startButtons.button( QDialogButtonBox.Cancel )
        QObject.connect( self.btn_About, SIGNAL( "clicked()" ), self.showAbout )

        #Startup
        self.startup()
        
        if self.cb_Raster.currentText() == "":
            QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "Please load and select a raster layer first" ) )
            self.close()
        if self.cb_Vector.currentText() == "":
            QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "Please load and select a vector layer" ) )
            self.close()  
        
    
    # Startup function
    def startup(self):
         # Load in raster and vector files
        vec = func.getVectorLayersNames()
        ras = func.getRasterLayersNames()
        self.cb_Raster.addItems( ras )
        self.cb_Vector.addItems( vec )
        
        # Unable most features
        self.EnableStuff("all")
    
    # Enable all necessary functions
    def EnableStuff(self,what):
        if(what == "YES"):
            self.stackWidget.setCurrentIndex(0)
            self.loadClasses() # load classes
            #self.cb_LClass.setEnabled( True )
            #self.rb_LCnumber.setEnabled( True )
            #self.rb_LCprop.setEnabled( True )
            #self.rb_Usum.setEnabled( False )
            #self.rb_Umean.setEnabled( False )
        if(what == "NO"):
            self.stackWidget.setCurrentIndex(1)
            #self.cb_LClass.setEnabled( False )
            #self.rb_LCnumber.setEnabled( False )
            #self.rb_LCprop.setEnabled( False )
            #self.rb_Usum.setEnabled( True )
            #self.rb_Umean.setEnabled( True )
        else:
            pass
            #self.cb_LClass.setEnabled( False )
            #self.rb_LCnumber.setEnabled( False )
            #self.rb_LCprop.setEnabled( False )
            #self.rb_Usum.setEnabled( False )
            #self.rb_Umean.setEnabled( False )
    
    # Get Raster classes
    def loadClasses(self):
        rasterName = func.getRasterLayerByName( self.cb_Raster.currentText() )
        if rasterName != "":
            rasterPath = rasterName.source()
            raster = gdal.Open(str(rasterPath))
            band = raster.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            array = band.ReadAsArray()
            self.classes = sorted(numpy.unique(array)) # get array of classes
            try:
                self.classes.remove(nodata) # Remove nodata-values from classes array
            except ValueError:
                try:
                    self.classes.remove(0)
                except ValueError:
                    pass
            classes = [str(numeric_cl) for numeric_cl in self.classes]
            self.cb_LClass.clear()
            self.cb_LClass.addItems( classes )
        else:
            self.cb_LClass.clear()
            self.cb_LClass.addItems( [""] )
            

    # Show feature count
    def featureCount(self, vectorName):
        if vectorName != "":
            # Load vector data
            self.vector = func.getVectorLayerByName( self.cb_Vector.currentText() )
            self.vectorPath = self.vector.source()
            nf = self.vector.featureCount()
            self.lab_feat.setText("Features ("+str(nf)+")")
        else:
            self.lab_feat.setText("Features (0)")

    # Show About Dialog
    def showAbout( self ):
        func.AboutDlg()
    
    # Runs the routine
    def go(self):
        if self.vector.geometryType() != QGis.Polygon:
            QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "This tool need the vector layer to have the geometry type: Polygons" ) )
            return
        if self.cb_Classified.currentIndex() == 0:
            QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "Please select the type of your raster layer (Classified|Unclassified)" ) )
            return
        cr1 = self.vector.crs()
        raster = func.getRasterLayerByName( self.cb_Raster.currentText() ) 
        cr2 = raster.crs()
        if cr1!=cr2:
            QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "Please make sure that vector and raster layer both posess the same spatial projection" ) )
            return
        
        t = self.cb_Classified.currentText()
        
        self.rasterPath = raster.source()
        
        bat = pov.BatchConverter(self.rasterPath,self.vectorPath)
        if(t == "YES"):
            #Calculate statistics for classified raster
            if(self.cb_LClass.currentText()==""):
                QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "Please select a valid landcover class!" ) )
                return
            else:
                cl = int(self.classes[self.cb_LClass.currentIndex()]) # Get selected class
            # Get Method
            if(self.rb_LCnumber.isChecked()):
                cmd = "LCnum"
            elif(self.rb_LCprop.isChecked()):
                cmd = "LCprop"
            
            results = bat.go(cmd,cl)
        elif(t == "NO"):
            #Calculate statistics for unclassified raster
            
            # Get Method
            if(self.rb_Usum.isChecked()):
                cmd = "sum"
            elif(self.rb_Umean.isChecked()):
                cmd = "mean"
            elif(self.rb_Ustd.isChecked()):
                cmd = "std"
            elif(self.rb_Umed.isChecked()):
                cmd = "med"
            elif(self.rb_Umax.isChecked()):
                cmd = "max"
            elif(self.rb_Umin.isChecked()):
                cmd = "min"
            elif(self.rb_Ulqt.isChecked()):
                cmd = "lowq"
            elif(self.rb_Uuqt.isChecked()):
                cmd = "uppq"

            results = bat.go(cmd,None)
        
        if(func.addAttributeToLayer(self.vector,cmd,results)):
            QMessageBox.information( self, self.tr( "Batch computing: Info" ),self.tr( "Calculated values were saved to provided vector layers attribute-table" ) )
        else:
            QMessageBox.warning( self, self.tr( "Batch computing: Warning" ),
                           self.tr( "There appeared an error while trying to save your values to the vector layers attribute-table" ) )

# Gui for generating a LandMod out of a rasterized map
class LandMod(QDialog, Ui_LandMod):
    def __init__(self, iface):
        # Initialize the Dialog
        QDialog.__init__( self )
        self.setupUi(self)
        self.iface = iface
        
        # Configure Connectors
        self.AcceptButton = self.buttonBox.button( QDialogButtonBox.Ok )
        self.closeButton = self.buttonBox.button( QDialogButtonBox.Cancel )
        QObject.connect( self.AcceptButton, SIGNAL( "clicked()" ), self.go )
        QObject.connect( self.btn_Save, SIGNAL( "clicked()" ), self.selectSaveFile )# Save File
        QObject.connect( self.cb_Raster, SIGNAL( "currentIndexChanged( QString )" ), self.cellSizer)
        QObject.connect( self.cb_Raster, SIGNAL( "currentIndexChanged( QString )" ), self.loadClasses)
        
        self.startup()
    
    # Configure GUI
    def startup(self):
        # Load in raster files
        self.cb_Raster.addItems( func.getRasterLayersNames() )
        if(self.cb_Raster.count()!=0):
            self.loadClasses()
            self.cellSizer(self.cb_Raster.currentText())
    
    # Set the cellsizer value 
    def cellSizer(self,rasterName):
        ras = func.getRasterLayerByName( rasterName )
        pixelSize = ras.rasterUnitsPerPixel()
        self.CellsizeLine.setEnabled( True )
        self.CellsizeLine.setText( QString(str(pixelSize)) ) 
    
    # Where to save the raster output
    def selectSaveFile( self ):   
        lastUsedDir = func.lastUsedDir()
        fileName = QFileDialog.getSaveFileName( self, self.tr( "Save raster as" ),\
        lastUsedDir, "GeoTIFF files (*.tif *.TIF)" )
        if fileName.isEmpty():
            return
        func.setLastUsedDir( fileName )
        # ensure the user never ommited the extension from the file name
        if not fileName.toLower().endsWith( ".tif" ):
            fileName += ".tif"
        self.where2Save.setText( fileName )
        self.where2Save.setEnabled( True ) 
    
    # Get Raster classes
    def loadClasses(self,rasterName=None):
        rasterName = func.getRasterLayerByName( self.cb_Raster.currentText() )
        if rasterName != "":
            rasterPath = rasterName.source()
            raster = gdal.Open(str(rasterPath))
            band = raster.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            array = band.ReadAsArray()
            self.classes = sorted(numpy.unique(array)) # get array of classes
            try:
                self.classes.remove(nodata) # Remove nodata-values from classes array
            except ValueError:
                try:
                    self.classes.remove(0)
                except ValueError:
                    pass
            classes = [str(numeric_cl) for numeric_cl in self.classes]
            self.cb_SelClass.clear()
            self.cb_SelClass.addItems( classes )
        else:
            self.cb_SelClass.clear()
            self.cb_SelClass.addItems( [""] )
    
    # Calculate new raster
    def go(self):
        if self.cb_Raster.currentIndex() == -1:
            QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                           self.tr( "Please load and select a classified raster first" ) )
            return
        if self.where2Save.text().isEmpty():
                QMessageBox.warning( self, self.tr( "LecoS: Warning" ),
                            self.tr( "Please give a destination where to save the results" ) )
                return
        # Get basic input
        raster = func.getRasterLayerByName( self.cb_Raster.currentText() )
        rasterPath = raster.source()
        cl = int(self.classes[self.cb_SelClass.currentIndex()]) # Get selected class
        savePath = str(self.where2Save.text())
        what = self.box_RasCalc.currentIndex()
        
        mod = lmod.LandscapeMod(rasterPath,cl)
        # Create class object
        if what == 0: # Patch Edges
            size = self.sp_EdgeMult.value()
            results = mod.extractEdges(size)
        elif what == 1: # Isolate smallest or greatest patch
            if self.rb_MaxMin1.isChecked():
                which = "min"
            else:
                which = "max"
            results = mod.getPatch(which)
        elif what == 2: # Increase/decrease landscape patches
            which = self.cb_IncDec.currentIndex()
            amount = self.sp_IncDecAm.value()
            results = mod.InDecPatch(which,amount)
        elif what == 3: # Fill holes inside landscape patches
            results = mod.closeHoles()
        elif what == 4: # Clean raster
            iter = self.sp_CleanIter.value()
            results = mod.cleanRaster(iter)
        
        # Save the results
        func.exportRaster(results,rasterPath,savePath)
        # Add to QGis if specified
        if self.addToToc.isChecked():
            func.rasterInQgis( savePath )

        