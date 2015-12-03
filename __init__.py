# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LecoS
                                 A QGIS plugin
 Contains analytical functions for landscape analysis
                             -------------------
        begin                : 2012-09-06
        copyright            : (C) 2012 by Martin Jung
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
 This script initializes the plugin, making it known to QGIS.
"""
def name():
    return "LecoS - Landscape Ecology statistics"
def description():
    return "Contains several analytical functions for land cover analysis"
def version():
    return "Version 2.0"
def icon():
    return "icons/icon.png"
def qgisMinimumVersion():
    return "2.0"
def classFactory(iface):
    # load LecoS class from file LecoS
    from lecos_main import LecoS
    return LecoS(iface)
