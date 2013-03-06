# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/dlg_DiversityDialog.ui'
#
# Created: Wed Oct 10 15:08:59 2012
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DivDialog(object):
    def setupUi(self, DivDialog):
        DivDialog.setObjectName(_fromUtf8("DivDialog"))
        DivDialog.resize(383, 133)
        self.horizontalLayoutWidget = QtGui.QWidget(DivDialog)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 361, 31))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(self.horizontalLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.cbRaster = QtGui.QComboBox(self.horizontalLayoutWidget)
        self.cbRaster.setObjectName(_fromUtf8("cbRaster"))
        self.horizontalLayout.addWidget(self.cbRaster)
        self.horizontalLayoutWidget_3 = QtGui.QWidget(DivDialog)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(10, 50, 361, 31))
        self.horizontalLayoutWidget_3.setObjectName(_fromUtf8("horizontalLayoutWidget_3"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_3.setMargin(0)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label_2 = QtGui.QLabel(self.horizontalLayoutWidget_3)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_3.addWidget(self.label_2)
        self.cbDivselect = QtGui.QComboBox(self.horizontalLayoutWidget_3)
        self.cbDivselect.setObjectName(_fromUtf8("cbDivselect"))
        self.horizontalLayout_3.addWidget(self.cbDivselect)
        self.btn_ok = QtGui.QDialogButtonBox(DivDialog)
        self.btn_ok.setGeometry(QtCore.QRect(90, 100, 171, 27))
        self.btn_ok.setOrientation(QtCore.Qt.Horizontal)
        self.btn_ok.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.btn_ok.setObjectName(_fromUtf8("btn_ok"))
        self.line = QtGui.QFrame(DivDialog)
        self.line.setGeometry(QtCore.QRect(10, 80, 361, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))

        self.retranslateUi(DivDialog)
        QtCore.QObject.connect(self.btn_ok, QtCore.SIGNAL(_fromUtf8("accepted()")), DivDialog.accept)
        QtCore.QObject.connect(self.btn_ok, QtCore.SIGNAL(_fromUtf8("rejected()")), DivDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DivDialog)

    def retranslateUi(self, DivDialog):
        DivDialog.setWindowTitle(QtGui.QApplication.translate("DivDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DivDialog", "Raster layer", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DivDialog", "Diversity index", None, QtGui.QApplication.UnicodeUTF8))

