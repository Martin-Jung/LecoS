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

# Import PyQT bindings
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import QGIS analysis tools
from qgis.core import *
from qgis.gui import *
from qgis.analysis import *

# Import base libraries
import os
import sys
import csv
import string
import math
import operator
import subprocess
import tempfile
import inspect

# Import numpy and scipy
import numpy
try:
    import scipy
except ImportError:
    QMessageBox.warning(QDialog(),"LecoS: Warning","Please install scipy (http://scipy.org/) in your QGIS python path.")
    sys.exit(0)
from scipy import ndimage # import ndimage module seperately for easy access

# Try to import PIL
try:
    import Image, ImageDraw
except ImportError:
    QMessageBox.warning(QDialog(),"LecoS: Warning","You need to have the image library PIL installed.")
    sys.exit(0)

# Try to import functions from osgeo
try:
    from osgeo import gdal
except ImportError:
    import gdal
try:
    from osgeo import ogr
except ImportError:
    import ogr
try:
    from osgeo import osr
except ImportError:
    import osr
try:
    from osgeo import gdal_array
except ImportError:
    import gdalnumeric
try:
    from osgeo import gdalconst
except ImportError:
    import gdalconst
    
# Register gdal and ogr drivers
if hasattr(gdal,"AllRegister"): # Can register drivers
    gdal.AllRegister() # register all gdal drivers
if hasattr(ogr,"RegisterAll"):
    ogr.RegisterAll() # register all ogr drivers

# Try to use exceptions with gdal and ogr
if hasattr(gdal,"UseExceptions"):
    gdal.UseExceptions()
if hasattr(ogr,"UseExceptions"):
    ogr.UseExceptions()

