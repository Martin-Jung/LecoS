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
import os,sys,csv,string,math,operator,subprocess,tempfile,inspect, time
from os import path

# Import functions and metrics
import lecos_functions as func
import landscape_statistics as lcs
import landscape_polygonoverlay as pov
import landscape_modifier as lmod

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

# Avoiding python 3 troubles
from __future__ import division

# Register gdal and ogr drivers
#if hasattr(gdal,"AllRegister"): # Can register drivers
#    gdal.AllRegister() # register all gdal drivers
#if hasattr(ogr,"RegisterAll"):
#    ogr.RegisterAll() # register all ogr drivers

# import Ui
from ui.dlg_landscapestatistics import Ui_Lecos
from ui.dlg_PolygonPerLandCover import Ui_BatchDialog
from ui.dlg_LandscapeModifier import Ui_LandMod

tmpdir = tempfile.gettempdir()

## CODE START ##
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
            self.NoDataVal.setToolTip(str("Please note that the nodata value must be an integer"))
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
            raster = gdal.Open(unicode(rasterPath))
            band = raster.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            self.NoDataVal.setEnabled( True )
            try:
                self.NoDataVal.setValidator(QDoubleValidator(-999999,999999,5))
            except TypeError: # Trying to catch up some strange Errors with this QT-Validator
                self.NoDataVal.setValidator(QDoubleValidator(-999999,999999,5,self))
                if isinstance(nodata,int)==False:
                    pass
                    #QMessageBox.warning( self, self.tr( "LecoS: Warning" ),self.tr( "Please format your rasters no-data value to integer (-99999 <-> 99999)" ) )

            self.NoDataVal.setText( unicode(nodata) )

    # Update Cellsize if a valid raster-file is selected
    def cellSizer( self, rasterName ):
        if rasterName != -1:
            if QGis.QGIS_VERSION_INT < 10900:
                pixelSize = func.getRasterLayerByName( rasterName ).rasterUnitsPerPixel()
            else:
                pixelSize = func.getRasterLayerByName( rasterName ).rasterUnitsPerPixelX() # Extract The X-Value
                pixelSizeY = func.getRasterLayerByName( rasterName ).rasterUnitsPerPixelY() # Extract The Y-Value
                # Check for rounded equal square cellsize
                if round(pixelSize,0) != round(pixelSizeY,0):
                    func.DisplayError(self.iface,"LecoS: Warning" ,"The cells in the layer %s are not square. Calculated values will be incorrect" % (rasterName),"WARNING")

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
        if len(fileName) == 0:
            return
        func.setLastUsedDir( fileName )
        # ensure the user never ommited the extension from the file name
        if not fileName.lower().endswith( ".csv" ):
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
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please load a classified landcover layer into QGis first","WARNING")
            return
        if self.rbSAVE.isChecked():
            if len(self.SaveCsv.text()) == 0:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please select where to save the results","WARNING")
                return
            if path.exists(self.SaveCsv.text()):
                func.DisplayError(self.iface,"LecoS: Warning" ,"File already exisits. Please select another path or delete file","WARNING")
                return
        if self.sp_cellsize.value() == 0:
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please entry a correct cellsize (greater zero)","WARNING")
            return

        # Values and Preset
        self.progressBar.setRange( 0, 4)
        self.progressBar.setValue( 0 ) # pb start

        raster = func.getRasterLayerByName( self.cbRaster.currentText() )
        rasterPath = raster.source()
        dataPath = self.SaveCsv.text()
        cellsize = self.sp_cellsize.value()
        try:
            nodata = float(self.NoDataVal.text())
        except ValueError:
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please set a correct nodata-value","WARNING")
            return

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
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please select a valid single metric","WARNING")

        ## Several Metrics
        elif(what == 1):
            metrics = []
            allitems = self.list_right.findItems("*", Qt.MatchWrap | Qt.MatchWildcard)
            if len(allitems)==0:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please select at least one item from the left list","WARNING")
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
                self.iface.mainWindow().statusBar().showMessage("Metric %s calculated" % (m))


        ## Landscape Metrics
        elif what == 2:
            metrics = []
            if self.ch_LC1.isChecked():
                metrics.append("LC_Mean")
            if self.ch_LC2.isChecked():
                metrics.append("LC_Sum")
            if self.ch_LC3.isChecked():
                metrics.append("LC_Min")
            if self.ch_LC4.isChecked():
                metrics.append("LC_Max")
            if self.ch_LC5.isChecked():
                metrics.append("LC_SD")
            if self.ch_LC6.isChecked():
                metrics.append("LC_LQua")
            if self.ch_LC7.isChecked():
                metrics.append("LC_Med")
            if self.ch_LC8.isChecked():
                metrics.append("LC_UQua")
            if self.ch_div1.isChecked():
                metrics.append("DIV_SH")
            if self.ch_div2.isChecked():
                metrics.append("DIV_EV")
            if self.ch_div3.isChecked():
                metrics.append("DIV_SI")
            if len(metrics)==0:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please select at least one item","WARNING")
                return
            # Processing
            try:
                int(nodata)
            except ValueError, TypeError:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please classify your raster with a correct integer nodata value","WARNING")
                return
            classes, array = lcs.f_landcover(rasterPath,nodata) # Get classes and value
            self.progressBar.setValue( self.progressBar.value() + 1 )
            # Looping through the selected metrics
            res = []
            res_tit = ["Metric","Value"]
            cl_analys = lcs.LandCoverAnalysis(array,cellsize,classes)
            for m in metrics:
                name, result = cl_analys.execLandMetric(m,nodata)
                self.progressBar.setValue( self.progressBar.value() + 1 )
                # Append Values to result class array
                res.append([name, result])
                self.iface.mainWindow().statusBar().showMessage("Metric %s calculated" % (m))

        self.progressBar.setValue( self.progressBar.value() + 1 )
        # Write results
        if self.rbSAVE.isChecked():
            func.DisplayError(self.iface,"LecoS: Info" ,"Results were successfully saved to file!","INFO")
            func.saveToCSV(res,res_tit,dataPath)
        else:
            func.DisplayError(self.iface,"LecoS: Info" ,"Calculations finished!","INFO")
            func.ShowResultTableDialog(res_tit, res)
        self.progressBar.setValue( self.progressBar.value() + 1 )
        self.close()

# Gui for batch computing Landcover for vector features
class BatchDialog(QDialog, Ui_BatchDialog):
    def __init__(self, iface):

        # Initialize the Dialog
        QDialog.__init__( self )

        self.setupUi(self)
        self.iface = iface

        # Connects
        QObject.connect( self.ch_selectAll, SIGNAL( "stateChanged( int )" ), self.SelectAllInList )
        QObject.connect( self.locateDir, SIGNAL( "clicked()" ), self.selectSaveFile )
        QObject.connect( self.cb_Raster, SIGNAL( "stateChanged()" ), self.EnableStuff ) # Enable Stuff
        QObject.connect( self.cb_Raster, SIGNAL( "stateChanged()" ), self.loadIDFields ) # Load IDFields
        QObject.connect( self.cb_Raster, SIGNAL( "currentIndexChanged( QString )" ), self.ListMetrics ) # Change Class metrics
        QObject.connect( self.cb_LClass, SIGNAL( "currentIndexChanged( QString )" ), self.vectorClass ) # Get Vector layers class values

        # Enable Stuff
        QObject.connect( self.cb_Raster, SIGNAL( "currentIndexChanged( QString )" ), self.EnableStuff) # Landscape
        QObject.connect( self.cb_Vector, SIGNAL( "currentIndexChanged( QString )" ), self.EnableStuff) # Poly overlay
        QObject.connect( self.rb_Landscape, SIGNAL( "clicked()" ), self.EnableStuff) # Change available stuff
        QObject.connect( self.rb_Class, SIGNAL( "clicked()" ), self.EnableStuff) # Change available stuff
        QObject.connect( self.ch_saveResult, SIGNAL( "stateChanged( int )" ), self.EnableStuff) # Change output

        # Button box
        #self.AcceptButton = self.startButtons.button( QDialogButtonBox.Ok )
        self.AcceptButton = self.startButtons.button( QDialogButtonBox.Ok )
        self.closeButton = self.startButtons.button( QDialogButtonBox.Cancel )
        #QObject.connect( self.AcceptButton, SIGNAL( "clicked()" ), self.go )
        #self.closeButton = self.startButtons.button( QDialogButtonBox.Cancel )
        QObject.connect( self.btn_About, SIGNAL( "clicked()" ), self.showAbout )

        #Startup
        self.startup()

    # Startup function
    def startup(self):
         # Load in landscape and vector files
        vec = func.getVectorLayersNames()
        ras = func.getRasterLayersNames()
        self.cb_Raster.addItems( ras + vec )
        self.cb_Vector.addItems( [""] + vec )

        self.ListMetrics()

        # Unable most features
        self.EnableStuff("default")

    # Load Class metrics
    def ListMetrics(self,ind=""):
        self.Cl_Metrics.clear()
        curLay = func.getLayerByName( self.cb_Raster.currentText() )
        if type(curLay) == QgsRasterLayer:
            stats = lcs.listStatistics()
            self.Cl_Metrics.addItems(stats)
        elif type(curLay) == QgsVectorLayer:
            stats = pov.listVectorStatistics()
            self.Cl_Metrics.addItems(stats)

    # Enable all necessary functions
    def EnableStuff(self,what=""):
        if what != "default":
            ras = func.getLayerByName( what )
            vec = func.getVectorLayerByName( what )
            land = self.cb_Raster.currentText() == what
            if self.rb_Class.isChecked(): # Check if Landscape or Class structures should be computed
                self.cb_LClass.setEnabled( True )
                # Disable General methods
                self.ch_LC1.setEnabled( False ),self.ch_LC2.setEnabled( False ),self.ch_LC3.setEnabled( False ),self.ch_LC4.setEnabled( False ),self.ch_LC5.setEnabled( False ),self.ch_LC6.setEnabled( False ),self.ch_LC7.setEnabled( False ),self.ch_LC8.setEnabled( False )
                # Disable Diversity methods
                self.ch_div1.setEnabled( False ),self.ch_div2.setEnabled( False ),self.ch_div3.setEnabled( False )
                # Set unchecked
                self.ch_LC1.setChecked( False ),self.ch_LC2.setChecked( False ),self.ch_LC3.setChecked( False ),self.ch_LC4.setChecked( False ),self.ch_LC5.setChecked( False ),self.ch_LC6.setChecked( False ),self.ch_LC7.setChecked( False ),self.ch_LC8.setChecked( False )
                # Disable Diversity methods
                self.ch_div1.setChecked( False ),self.ch_div2.setChecked( False ),self.ch_div3.setChecked( False )
                # Enable Class metrics
                self.Cl_Metrics.setEnabled( True )
                self.ch_selectAll.setEnabled( True )
            elif self.rb_Landscape.isChecked():
                # Enable General methods
                self.ch_LC1.setEnabled( True ),self.ch_LC2.setEnabled( True ),self.ch_LC3.setEnabled( True ),self.ch_LC4.setEnabled( True ),self.ch_LC5.setEnabled( True ),self.ch_LC6.setEnabled( True ),self.ch_LC7.setEnabled( True ),self.ch_LC8.setEnabled( True )
                # Disable Diversity methods
                self.ch_div1.setEnabled( True ),self.ch_div2.setEnabled( True ),self.ch_div3.setEnabled( True )
                self.cb_LClass.setEnabled( False )
                # Enable Class metrics
                self.Cl_Metrics.setEnabled( False )
                self.ch_selectAll.setEnabled( False )
                # Clear classes
                self.cb_LClass.clear()

            # TODO: Vector grid overlay
            # Disable vector grid overlay field
            if type(ras) == QgsVectorLayer and land:
                if self.ClassLayout.count() != 3:
                    self.VCl = QComboBox()
                    self.VCl.setEnabled( False )
                    self.ClassLayout.insertWidget(2,self.VCl)
                self.cb_Vector.setEnabled( False )
                self.cb_Vector.setCurrentIndex(0)
                self.cb_SelD.setEnabled( True )
                self.loadIDFields()
                self.ch_addToTable.setEnabled( False ) # Disable add to attribute table for inherent vector layers
                self.ch_addToTable.setChecked( False )
                if self.rb_Landscape.isChecked():
                    self.ch_div1.setEnabled( False ),self.ch_div2.setEnabled( False ),self.ch_div3.setEnabled( False )

            elif (type(ras) == QgsRasterLayer) and land:
                # Delete Class Vector widget if available
                if self.ClassLayout.count() == 3:
                    self.VCl.hide()
                    self.ClassLayout.removeWidget(self.VCl)
                self.cb_Vector.setEnabled( True )
                #self.cb_SelD.setEnabled( False )
                self.ch_addToTable.setEnabled( True )
                if self.rb_Landscape.isChecked():
                    self.ch_div1.setEnabled( True ),self.ch_div2.setEnabled( True ),self.ch_div3.setEnabled( True )
                else:
                    self.ch_div1.setEnabled( False ),self.ch_div2.setEnabled( False ),self.ch_div3.setEnabled( False )

            # Enable and load classes
            curLay = func.getLayerByName( self.cb_Raster.currentText() )
            if type(ras) == QgsRasterLayer or type(curLay) == QgsRasterLayer:
                if self.rb_Class.isChecked():
                    self.cb_LClass.setEnabled( True )
                    self.loadClasses("ras") # load classes
            elif type(ras) == QgsVectorLayer or type(curLay) == QgsVectorLayer:
                if self.rb_Class.isChecked():
                    self.cb_LClass.setEnabled( True )
                    self.loadClasses("vec") # load classes
                    self.loadIDFields() # load ID fields

            # Enable ID field for vector overlay
            vecOV = func.getVectorLayerByName( self.cb_Vector.currentText() )
            if type(curLay) == QgsRasterLayer:
                if type(vecOV) == QgsVectorLayer and vecOV != "":
                    self.cb_SelD.setEnabled( True )
                    self.loadIDFields()
                else:
                    self.cb_SelD.setEnabled( False )
                    self.cb_SelD.clear()

            # Check Status of output
            if self.ch_saveResult.isChecked():
                self.where2Save.setEnabled( True )
                self.locateDir.setEnabled( True )
            else:
                self.where2Save.setEnabled( False )
                self.locateDir.setEnabled( False )

        else:
            self.Cl_Metrics.setEnabled( False )
            self.ch_selectAll.setEnabled( False )
            self.cb_LClass.setEnabled( False )
            self.cb_SelD.setEnabled( False )


    # Load ID fields
    def loadIDFields(self):
        vectorName = func.getLayerByName( self.cb_Raster.currentText() )
        test = func.getVectorLayerByName( self.cb_Vector.currentText() )
        if test != "" and type(vectorName) == QgsVectorLayer:
            self.cb_SelD.setEnabled( True )
            self.cb_SelD.clear()
            fields = func.getFieldList( vectorName )
            if QGis.QGIS_VERSION_INT >= 10900:
                for field in fields:
                    if field.type() in [ QVariant.Int, QVariant.String ]:
                        self.cb_SelD.addItem( field.name() )
            else:
                prov = vectorName.dataProvider()
                for k,  field in prov.items():
                    if field.type() in [ QVariant.Int, QVariant.String ]:
                        self.cb_SelD.addItem( field.name() )

        else: # RasterLayer is current layer
            self.cb_SelD.setEnabled( True )
            self.cb_SelD.clear()
            # Load Grouping ID for vector field and table output
            fields = func.getFieldList( test )
            for field in fields:
                self.cb_SelD.addItem( field.name() )

    # Get landscape classes
    def loadClasses(self,typ):
        if typ == "ras":
            rasterName = func.getRasterLayerByName( self.cb_Raster.currentText() )
            if rasterName != "":
                rasterPath = rasterName.source()
                raster = gdal.Open(unicode(rasterPath))
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
        elif typ == "vec":
            vectorName = func.getVectorLayerByName( self.cb_Raster.currentText() )
            if vectorName != "":
                self.cb_LClass.clear()
                fields = func.getFieldList( vectorName )
                self.classes = []
                if QGis.QGIS_VERSION_INT >= 10900:
                    for field in fields:
                        if field.type() in [ QVariant.Int, QVariant.Double, QVariant.String ]:
                            self.cb_LClass.addItem( field.name() )
                            self.classes.append(field.name())
                else:
                    prov = vectorName.dataProvider()
                    for k,  field in prov.items():
                        if field.type() in [ QVariant.Int, QVariant.Double, QVariant.String ]:
                            self.cb_LClass.addItem( field.name() )
                            self.classes.append(field.name())
            else:
                self.cb_LClass.clear()

    # Load Vector classes from attribute table
    def vectorClass(self,cl):
        vectorName = func.getLayerByName( self.cb_Raster.currentText() )
        if type(vectorName) == QgsVectorLayer:
            cur = unicode(self.cb_LClass.currentText())
            if cur != "":
                self.VCl.clear()
                self.VCl.setEnabled( True )
                attr = func.getAttributeList(vectorName,cur)
                self.VecAttr = []
                for field in attr:
                    self.VCl.addItem( str(field) )
                    self.VecAttr.append(field)

    # Select all Class metrics
    def SelectAllInList(self, state):
        if state == Qt.Checked:
            allitems = self.Cl_Metrics.findItems("*", Qt.MatchWrap | Qt.MatchWildcard)
            for item in allitems:
                item.setSelected( True )
            self.ch_selectAll.setText("Unselect all")
        elif state == Qt.Unchecked:
            self.Cl_Metrics.clearSelection()
            self.ch_selectAll.setText("Select all")

    # Where to save the csv
    def selectSaveFile( self ):
        lastUsedDir = func.lastUsedDir()
        fileName = QFileDialog.getSaveFileName( self, self.tr( "Save data as" ),\
        lastUsedDir, "CSV files (*.csv *.CSV)" )
        if len(fileName) < 1:
            return
        func.setLastUsedDir( fileName )
        # ensure the user never ommited the extension from the file name
        if not fileName.lower().endswith( ".csv" ):
            fileName += ".csv"
        self.where2Save.setText( fileName )
        self.where2Save.setEnabled( True )

#     # Show feature count
#     def featureCount(self, vectorName):
#         if vectorName != "":
#             # Load vector data
#             self.vector = func.getVectorLayerByName( self.cb_Vector.currentText() )
#             self.vectorPath = self.vector.source()
#             nf = self.vector.featureCount()
#             self.lab_feat.setText("Features ("+str(nf)+")")
#         else:
#             self.lab_feat.setText("Features (0)")

    # Show About Dialog
    def showAbout( self ):
        func.AboutDlg()

    # Returns the selected metrics
    def getSelMetric(self):
        res = []
        m = self.Cl_Metrics.selectedItems()
        for item in m:
            res.append(str( item.text() ))
        # Other Metrics ?
        if self.ch_LC1.isChecked():
            res.append("LC_Mean")
        if self.ch_LC2.isChecked():
            res.append("LC_Sum")
        if self.ch_LC3.isChecked():
            res.append("LC_Min")
        if self.ch_LC4.isChecked():
            res.append("LC_Max")
        if self.ch_LC5.isChecked():
            res.append("LC_SD")
        if self.ch_LC6.isChecked():
            res.append("LC_LQua")
        if self.ch_LC7.isChecked():
            res.append("LC_Med")
        if self.ch_LC8.isChecked():
            res.append("LC_UQua")
        if self.ch_div1.isChecked():
            res.append("DIV_SH")
        if self.ch_div2.isChecked():
            res.append("DIV_EV")
        if self.ch_div3.isChecked():
            res.append("DIV_SI")
        return res

    # Runs the routine
    def accept(self):
        # Error catching and variable returning
        if self.cb_Raster.currentIndex() == -1:
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please load and select a classified landscape layer first","WARNING")
            return
        self.landscape = func.getLayerByName( self.cb_Raster.currentText() )
        self.landPath = self.landscape.source()

        if type(self.landscape) == QgsVectorLayer: # Check if landscape vector layer is a polygon
            if self.landscape.geometryType() != QGis.Polygon:
                func.DisplayError(self.iface,"LecoS: Warning" ,"The landscape layer have to be of geometry type: Polygons","WARNING")
                return
        # Default values
        self.vector = None
        self.vectorPath = None
        # Load in overlaying Grid and raise error if not a polygon or no landscape raster
        if self.cb_Vector.currentText() != "":
            self.vector = func.getVectorLayerByName( self.cb_Vector.currentText() )
            self.vectorPath = self.vector.source()
            if type(self.landscape) == QgsVectorLayer:
                if self.landscape.geometryType() != QGis.Polygon:
                    func.DisplayError(self.iface,"LecoS: Warning" ,"This tool need the vector grid to have the geometry type: Polygon","WARNING")
                    return
            # Check if both layers have the same projection
            cr1 = self.vector.crs()
            cr2 = self.landscape.crs()
            if cr1!=cr2:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please make sure that both layers have the same spatial projection","WARNING")
                return
            # Check if a layer has been chosen twice
            if self.landPath == self.vectorPath:
                func.DisplayError(self.iface,"LecoS: Warning" ,"It is not possible to overlay layers from the same source. Specify a Grouping ID","WARNING")
                return
        elif type(self.landscape) == QgsRasterLayer:
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please load and select an overlaying vector grid","WARNING")
            return
        elif type(self.landscape) == QgsVectorLayer:
            if self.cb_SelD.currentText() == "":
                func.DisplayError(self.iface,"LecoS: Warning" ,"You didn't choose an overlaying vector grid and therefore need to specify a grouping ID","WARNING")
                return

        if self.rb_Landscape.isChecked(): # Landscape or Class metrics
            self.cl_metric = False
            self.classIND = None
        else:
            self.cl_metric = True
            self.classIND = self.cb_LClass.currentText()
        # The ID
        self.LandID = self.cb_SelD.currentText()

        self.metrics = self.getSelMetric() # Get list of all Metrics
        if len(self.metrics) == 0:
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please select at least one metric to compute!","WARNING")
            return
        if self.ch_saveResult.isChecked():
            self.FileSave = True
            self.FileSavePath = self.where2Save.text()
            # If no output has been defined -> create a temporary file
            if self.FileSavePath == "Select a destination or leave blank to create a temporary file":
                self.FileSavePath = tmpdir+os.path.sep+"temp_"+str(self.cb_Raster.currentText())+"_"+str(int(time.time()))+"_results.csv"
        else:
            self.FileSave = False
        if self.ch_addToTable.isChecked(): # Add to Attribute Table
            self.Add2Table = True
        else:
            self.Add2Table = False

        ## Processing Start
        ### Vector part
        if type(self.landscape) == QgsVectorLayer:
            if self.cb_Vector.currentText() == "":
                # Use inherent vector grouping id
                #self.classIND
                if self.cl_metric:
                    # Analysis with a given vector class field
                    if(self.classIND == ""):
                        func.DisplayError(self.iface,"LecoS: Warning" ,"Please select a valid landcover class!","WARNING")
                        return
                    else:
                        clf = self.classes[self.cb_LClass.currentIndex()] # Get selected classField
                        bat = pov.VectorBatchConverter(self.landscape,self.LandID,clf,self.iface)
                        cl =  self.VecAttr[self.VCl.currentIndex()] # Get selected class in field
                        results = []
                        for cmd in self.metrics:
                            results.append(bat.go(cmd,cl))
                            self.iface.mainWindow().statusBar().showMessage("Metric %s calculated" % (cmd))
                        self.Output(results)
                else:
                    # Vector analysis on Landscape Level
                    bat = pov.VectorBatchConverter(self.landscape,self.LandID)
                    results = []
                    for el in ('LC','DIV'):
                        met = filter(lambda x:el in x,self.metrics)
                        for cmd in met:
                            results.append(bat.go(cmd))
                            self.iface.mainWindow().statusBar().showMessage("Metric %s calculated" % (cmd))
                    self.Output(results)

            else:
                # Use overlaying vector grid  -> need to cut landscape vectors first
                #TODO: vector grid overlay
                pass
        ### Raster part
        if type(self.landscape) == QgsRasterLayer:
            # Get None Nulldata Error
            try:
                image = gdal.Open(unicode(self.landPath))
                band = image.GetRasterBand(1)
                nd = band.GetNoDataValue()
                int(nd)
            except TypeError, ValueError:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Please classify your raster with a correct nodata value","WARNING")
                return
            # Check if polygon is correctly set
            try:
                v = ogr.Open(unicode( self.vectorPath ))
                l = v.GetLayer()
                l.GetFeature(0).GetGeometryRef()
            except AttributeError:
                func.DisplayError(self.iface,"LecoS: Warning" ,"There is something wrong with your polygon layer. Try to save it to a new file.","WARNING")
                return
            # Look for smaller rasters than polygons
            rasE = self.landscape.extent()
#            vecE = self.vector.extent()
#            if vecE > rasE:
#                func.DisplayError(self.iface,"LecoS: Warning" ,"Please cut the overlaying vector to the rasters extent","WARNING")
#                return
            bat = pov.BatchConverter(self.landPath,self.vectorPath,self.iface)
            # Landscape or classified
            if self.cl_metric:
                if(self.classIND == ""):
                    func.DisplayError(self.iface,"LecoS: Warning" ,"Please select a valid landcover class!","WARNING")
                    return
                else:
                    cl = int(self.classes[self.cb_LClass.currentIndex()]) # Get selected class

                if QGis.QGIS_VERSION_INT < 10900:
                    cellsize = self.landscape.rasterUnitsPerPixel()
                else:
                    cellsize = self.landscape.rasterUnitsPerPixelX() # Extract The X-Value
                    cellsizeY = self.landscape.rasterUnitsPerPixelY() # Extract The Y-Value
                    # Check for rounded equal square cellsize
                    if round(cellsize,0) != round(cellsizeY,0):
                        func.DisplayError(self.iface,"LecoS: Warning" ,"The cells in the layer %s are not square. Calculated values will be incorrect" % (self.cb_Raster.currentText()),"WARNING")

                #Calculate selected statistics for classified raster
                results = []
                error = 0
                for cmd in self.metrics:
                    err, r = bat.go(cmd,cl,cellsize,None,rasE)
                    results.append(r)
                    error = error + len(err)
                self.DLmessagebar(error,err)
                self.Output(results)
            else:
                if QGis.QGIS_VERSION_INT < 10900:
                    cellsize = self.landscape.rasterUnitsPerPixel()
                else:
                    cellsize = self.landscape.rasterUnitsPerPixelX() # Extract The X-Value
                    cellsizeY = self.landscape.rasterUnitsPerPixelY() # Extract The Y-Value
                    # Check for rounded equal square cellsize
                    if round(cellsize,0) != round(cellsizeY,0):
                        func.DisplayError(self.iface,"LecoS: Warning" ,"The cells in the layer %s are not square. Calculated values will be incorrect" % (self.cb_Raster.currentText()),"WARNING")
                #Calculate statistics for unclassified raster
                results = []
                error = 0
                for el in ('LC','DIV'):
                    met = filter(lambda x:el in x,self.metrics)
                    for cmd in met:
                        err, r = bat.go(cmd,None,cellsize,None,rasE)
                        results.append(r)
                        error = error + len(err)
                self.DLmessagebar(error,err)
                self.Output(results)

    # Dialog for to messagebar
    def DLmessagebar(self,n,err):
        if n > 0 and QGis.QGIS_VERSION_INT >= 10900:
            error = str(n / len(self.metrics))

            text = "There were no overlay values for "+error+" vector features. All features unable to compute are selected now for inspectation."
            widget = self.iface.messageBar().createMessage("LecoS - Warning",text)
            # Combobox for selecting. Not found entries selected
            #btn = QComboBox()
            #QObject.connect( btn, SIGNAL( "currentIndexChanged( QString )" ), self.selectFeatID )
            #widget.layout().addWidget(btn)
            #self.iface.messageBar().pushWidget(widget, QgsMessageBar.WARNING)
            #for item in err:
            #   btn.addItem(str(item))
            #return btn
            for item in err:
                self.selectFeatID(item)

    # Select features with ID
    def selectFeatID(self,ID):
        ID = int(ID)
        self.vector.select(ID)

    # Function for Output generation
    def Output(self,results):
        if self.Add2Table:
            # Add to overlaying vector grid
            add = func.addAttributesToLayer(self.vector,results)
            if add == False:
                func.DisplayError(self.iface,"LecoS: Warning" ,"Values couldn't be added to the attribute table","WARNING")
            else:
                func.DisplayError(self.iface,"LecoS: Info" ,"Values were added to the vector layers attribute table","INFO")
        if self.FileSave:
            # Write to file
            if type(self.landscape) == QgsVectorLayer:
                title = ["GroupingField"]
            else:
                title = ["PolygonFeatureID"]
                # Add grouping ID if selected
                if self.LandID != "" or None:
                    title.append(str(self.LandID))
            for x in results:
                try: # Catch in case there are no results
                    title.append( str(x[0][1]) )
                except IndexError:
                    func.DisplayError(self.iface,"LecoS: Warning" ,"Results couldn't be calculated. Please make sure all shapes are within the rasters extent!","WARNING")
                    return
            f = open(self.FileSavePath, "wb" )
            writer = csv.writer(f,delimiter=';',quotechar="",quoting=csv.QUOTE_NONE)
            writer.writerow(title)
            # Get values of Overlay grouping ID
            if type(self.landscape) == QgsRasterLayer:
                if self.LandID != "" or None:
                    attr = func.getAttributeList(self.vector,self.LandID)
            # Get number of polygon features
            feat = range(0,len(results[0]))
            for feature in feat: # Write feature to new line
                if type(self.landscape) == QgsVectorLayer:
                    r = [results[0][feature][0]]
                else:
                    r = [feature]
                    # Add Grouping Field value
                    if self.LandID != "" or None:
                        r.append(attr[feature])
                for item in results:
                    r.append(item[feature][2])
                writer.writerow(r)
            f.close()
            func.DisplayError(self.iface,"LecoS: Info" ,"Landcover statistics were successfully written to file","INFO")

        if (self.Add2Table == False) and (self.FileSave == False):
            # Direct Output?
            if type(self.landscape) == QgsVectorLayer:
                title = ["GroupingField"]
            else:
                title = ["PolygonFeatureID"]
            for x in results:
                title.append( str(x[0][1]) )
            w = func.ShowResultTableDialog2(title,results)
            if w:
                func.DisplayError(self.iface,"LecoS: Info" ,"Landcover statistics were successfully calculated","INFO")
            else:
                func.DisplayError(self.iface,"LecoS: Warning" ,"An error occured while attempting to display the results table","WARNING")

        # Add result to QGIS
        if self.ch_AddQGIS.isChecked() and self.ch_saveResult.isChecked():
            func.tableInQgis( self.FileSavePath )

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
            #self.cellSizer(self.cb_Raster.currentText())

    # Set the cellsizer value
    def cellSizer(self,rasterName):
        ras = func.getRasterLayerByName( rasterName )
        if QGis.QGIS_VERSION_INT < 10900:
            pixelSize = ras.rasterUnitsPerPixel()
        else:
            pixelSize = ras.rasterUnitsPerPixelX() # Extract The X-Value
            pixelSizeY = ras.rasterUnitsPerPixelY() # Extract The Y-Value
            # Check for rounded equal square cellsize
            if round(pixelSize,0) != round(pixelSizeY,0):
                func.DisplayError(self.iface,"LecoS: Warning" ,"The cells in the layer %s are not square. Calculated values will be incorrect" % (rasterName),"WARNING")

        self.CellsizeLine.setEnabled( True )
        self.CellsizeLine.setText( str(pixelSize) )

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
            raster = gdal.Open(unicode(rasterPath))
            band = raster.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            if nodata == None: # raise error
                func.DisplayError(self.iface,"LecoS: Warning" ,"The layer %s has no valid no-data value (no number)!" % (self.cb_Raster.currentText()),"CRITICAL")

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
            func.DisplayError(self.iface,"LecoS: Warning" ,"Please load and select a classified raster first","WARNING")
            return
        savePath = str(self.where2Save.text())
        if savePath == "": # If no output has been defined -> create a temporary file
            savePath = tmpdir+os.path.sep+"temporary_raster.tif"

        # Get basic input
        raster = func.getRasterLayerByName( self.cb_Raster.currentText() )
        rasterPath = raster.source()
        cl = int(self.classes[self.cb_SelClass.currentIndex()]) # Get selected class

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
        func.DisplayError(self.iface,"LecoS: Info" ,"Successfully generated modified raster layer","INFO")

        # Add to QGis if specified
        if self.addToToc.isChecked():
            func.rasterInQgis( savePath )


