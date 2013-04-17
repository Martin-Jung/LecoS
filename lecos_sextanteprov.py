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

from sextante.core.AlgorithmProvider import AlgorithmProvider
from sextante.core.SextanteConfig import Setting, SextanteConfig
from lecos_sextantealgorithms import *

class LecoSAlgorithmsProv(AlgorithmProvider):

    MY_DUMMY_SETTING = "MY_DUMMY_SETTING"

    def __init__(self):
        AlgorithmProvider.__init__(self)
        self.alglist = [ExampleAlgorithm()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        '''In this method we add settings needed to configure our provider.
        Do not forget to call the parent method, since it takes care or
        automatically adding a setting for activating or deactivating the
        algorithms in the provider'''
        AlgorithmProvider.initializeSettings(self)
        SextanteConfig.addSetting(Setting("LecoS", LecoSAlgorithmsProv.MY_DUMMY_SETTING, "Example setting", "Default value"))
        '''To get the parameter of a setting parameter, use SextanteConfig.getSetting(name_of_parameter)'''

    def unload(self):
        '''Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded'''
        AlgorithmProvider.unload(self)
        SextanteConfig.removeSetting( LecoSAlgorithmsProv.MY_DUMMY_SETTING)


    def getName(self):
        '''This is the name that will appear on the toolbox group.
        It is also used to create the command line name of all the algorithms
        from this provider'''
        return "Example algorithms"

    def getIcon(self):
        '''We return the default icon'''
        return AlgorithmProvider.getIcon(self)


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
        self.algs = self.alglist