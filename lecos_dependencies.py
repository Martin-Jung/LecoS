# -*- coding: utf-8 -*-
from __future__ import absolute_import

import importlib

from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsProcessingException


class MissingDependencyError(ImportError):
    pass


SCIPY_REQUIRED_MESSAGE = (
    "LecoS requires scipy in the QGIS Python environment. "
    "Install scipy and restart QGIS."
)

POLYGON_OVERLAY_REQUIRED_MESSAGE = (
    "LecoS landscape vector overlay requires scipy and Pillow in the QGIS "
    "Python environment. Install the missing dependencies and restart QGIS."
)

NLMPY_REQUIRED_MESSAGE = (
    "LecoS neutral landscape model tools require scipy and an nlmpy package "
    "that is compatible with the active QGIS Python environment. Install a "
    "supported nlmpy version or leave these optional tools disabled."
)


def show_missing_dependency(message):
    QMessageBox.critical(QDialog(), "LecoS: Missing dependency", message)


def require_runtime_dependency(is_available, message):
    if not is_available:
        raise MissingDependencyError(message)


def require_processing_dependency(is_available, message):
    if not is_available:
        raise QgsProcessingException(message)


def load_optional_nlmpy_module():
    try:
        return importlib.import_module("nlmpy.nlmpy")
    except Exception:
        return None