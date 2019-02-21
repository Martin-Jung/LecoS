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

from qgis.PyQt.QtCore import *
/***************************************************************************
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
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

# Sextante bindings
from qgis.core import QgsProcessingProvider as AlgorithmProvider
from .lecos_sextantealgorithms import *

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
    from .nlmpy_sextantewrapper import *


class LecoSAlgorithmsProv(AlgorithmProvider):
    tmpdir = tmpdir
    def __init__(self):
        super().__init__()
        # Create algorithms list
        self.algs = []
    def id(self):
        return "lecos"
    def name(self):
        '''This is the name that will appear on the toolbox group.
        It is also used to create the command line name of all the algorithms
        from this provider'''
        return "LecoS"
    def icon(self):
        '''We return the icon for lecos'''
        return QIcon(os.path.join(os.path.dirname(__file__), "icons", "icon.png"))
    def getDescription(self):
        return "LecoS (Landscape ecology statistics)"
    def load(self):
        self.refreshAlgorithms()
        return True
    def unload(self):
        '''Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded'''
        pass
    def isActive(self):
        return True
    def setActive(self, active):
        pass   
    def getAlgs(self):
        algs = [CreateRandomLandscape()]        
        # Load in Algorithms from lecos_sextantealgorithms
        # Landscape preperation
        
        algs.append( MatchLandscapes() )
        algs.append( RasterWithRasterClip() )
        
        # Landscape statistics
        algs.append( LandscapeStatistics() )
        algs.append( PatchStatistics() )
        algs.append( CountRasterCells() )
        algs.append( ZonalStatistics() )
        
        # Landscape Vector Overlay
        algs.append( RasterPolyOver() )
        algs.append( GetRasterValuesPoint() )
        #algs.append( VectorPolyOver() )
        
                
        # Landscape modifications
        algs.append( LabelLandscapePatches() )
        algs.append( NeighbourhoodAnalysis() )
        algs.append( IncreaseLandPatch() )
        algs.append( ExtractEdges() )
        algs.append( IsolateExtremePatch() )
        algs.append( CloseHoles() )
        algs.append( CleanSmallPixels() )
        
        # TODO: Won't work
        # NLMPY if available
        """
        if nlmpy:
            algs.append( RandomElementNN() )
            
            algs.append( RandomClusterNN() )
            algs.append( LinearRescale01() )
            algs.append( RandomUniformed01() )
            algs.append( SpatialRandom() )
            algs.append( PlanarGradient() )
            algs.append( EdgeGradient() )
            algs.append( DistanceGradient() )
            algs.append( MidpointDisplacement() )
            algs.append( RandomRectangularCluster() )
            algs.append( MeanOfCluster() )
            algs.append( ClassifyArray() )
            """
        return algs
    
    def loadAlgorithms(self):
        '''Create list of Arguments'''
        self.algs = self.getAlgs()
        for a in self.algs:
            self.addAlgorithm(a)
    def tr(self, string, context=''):
        pass