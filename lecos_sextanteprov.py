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

# Sextante bindings
from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.core.ProcessingLog import ProcessingLog
from lecos_sextantealgorithms import *

# Import modules
import tempfile
tmpdir = tempfile.gettempdir() # tempdir
import os

# NLMPY
nlmpy = False
try:
    import nlmpy
except ImportError:
    nlmpy = True
if nlmpy:
    from nlmpy_sextantewrapper import *


class LecoSAlgorithmsProv(AlgorithmProvider):

    tmpdir = tmpdir

    def __init__(self):
        AlgorithmProvider.__init__(self)
        # Create algorithms list
        self.createAlgsList()
    
    def getDescription(self):
        return "LecoS (Landscape ecology statistics)"

    def initializeSettings(self):
        '''In this method we add settings needed to configure our provider.
        Do not forget to call the parent method, since it takes care or
        automatically adding a setting for activating or deactivating the
        algorithms in the provider'''
        AlgorithmProvider.initializeSettings(self)
        #SextanteConfig.addSetting(Setting(self.getDescription(), LecoSAlgorithmsProv.tmpdir, "Temporary Directory", tmpdir))
        '''To get the parameter of a setting parameter, use SextanteConfig.getSetting(name_of_parameter)'''

    def unload(self):
        '''Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded'''
        AlgorithmProvider.unload(self)
        #SextanteConfig.removeSetting(LecoSAlgorithmsProv.tmpdir)

    def getName(self):
        '''This is the name that will appear on the toolbox group.
        It is also used to create the command line name of all the algorithms
        from this provider'''
        return "lecos"

    def getIcon(self):
        '''We return the icon for lecos'''
        return QIcon(os.path.dirname(__file__) + os.sep+"icons"+os.sep+"icon.png")
    
    def createAlgsList(self):
        '''Create list of Arguments'''
        
        self.preloadedAlgs = []        
        # Load in Algorithms from lecos_sextantealgorithms

        # Landscape preperation
        self.preloadedAlgs.append( CreateRandomLandscape() )        
        self.preloadedAlgs.append( MatchLandscapes() )
        self.preloadedAlgs.append( RasterWithRasterClip() )
        
        # Landscape statistics
        self.preloadedAlgs.append( LandscapeStatistics() )
        self.preloadedAlgs.append( PatchStatistics() )
        self.preloadedAlgs.append( CountRasterCells() )
        self.preloadedAlgs.append( ZonalStatistics() )

        # Landscape Vector Overlay
        self.preloadedAlgs.append( RasterPolyOver() )
        self.preloadedAlgs.append( GetRasterValuesPoint() )
        #self.preloadedAlgs.append( VectorPolyOver() )
                
        # Landscape modifications
        self.preloadedAlgs.append( LabelLandscapePatches() )
        self.preloadedAlgs.append( NeighbourhoodAnalysis() )
        self.preloadedAlgs.append( IncreaseLandPatch() )
        self.preloadedAlgs.append( ExtractEdges() )
        self.preloadedAlgs.append( IsolateExtremePatch() )
        self.preloadedAlgs.append( CloseHoles() )
        self.preloadedAlgs.append( CleanSmallPixels() )
        
        # NLMPY if available
        if nlmpy:
            self.preloadedAlgs.append( RandomElementNN() )
            self.preloadedAlgs.append( RandomClusterNN() )
            self.preloadedAlgs.append( LinearRescale01() )
            self.preloadedAlgs.append( RandomUniformed01() )
            self.preloadedAlgs.append( SpatialRandom() )
            self.preloadedAlgs.append( PlanarGradient() )
            self.preloadedAlgs.append( EdgeGradient() )
            self.preloadedAlgs.append( DistanceGradient() )
            self.preloadedAlgs.append( MidpointDisplacement() )
            self.preloadedAlgs.append( RandomRectangularCluster() )
            self.preloadedAlgs.append( MeanOfCluster() )
            self.preloadedAlgs.append( ClassifyArray() )
            
        
        for alg in self.preloadedAlgs:
            alg.provider = self # reset provider

    
    def _loadAlgorithms(self):
        '''Here we fill the list of algorithms in self.algs.
        This method is called whenever the list of algorithms should be updated.
        If the list of algorithms can change while executing SEXTANTE for QGIS
        (for instance, if it contains algorithms from user-defined scripts and
        a new script might have been added), you should create the list again
        here.
        In this case, since the list is always the same, we assign from the pre-made list.
        This assignment has to be done in this method even if the list does not change,
        since the self.algs list is cleared before calling this method'''
        self.algs = self.preloadedAlgs