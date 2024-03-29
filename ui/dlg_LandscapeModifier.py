# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\caioh\src\LecoS\ui\dlg_LandscapeModifier.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LandMod(object):
    def setupUi(self, LandMod):
        LandMod.setObjectName("LandMod")
        LandMod.resize(487, 403)
        LandMod.setMinimumSize(QtCore.QSize(487, 333))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Modify_Res/icons/icon_LandMod.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LandMod.setWindowIcon(icon)
        self.horizontalLayoutWidget = QtWidgets.QWidget(LandMod)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(9, 9, 471, 29))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cb_Raster = QtWidgets.QComboBox(self.horizontalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_Raster.sizePolicy().hasHeightForWidth())
        self.cb_Raster.setSizePolicy(sizePolicy)
        self.cb_Raster.setFrame(True)
        self.cb_Raster.setObjectName("cb_Raster")
        self.horizontalLayout.addWidget(self.cb_Raster)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.cb_SelClass = QtWidgets.QComboBox(self.horizontalLayoutWidget)
        self.cb_SelClass.setObjectName("cb_SelClass")
        self.horizontalLayout.addWidget(self.cb_SelClass)
        self.line = QtWidgets.QFrame(LandMod)
        self.line.setGeometry(QtCore.QRect(10, 70, 471, 16))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.box_RasCalc = QtWidgets.QToolBox(LandMod)
        self.box_RasCalc.setGeometry(QtCore.QRect(10, 80, 471, 271))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.box_RasCalc.sizePolicy().hasHeightForWidth())
        self.box_RasCalc.setSizePolicy(sizePolicy)
        self.box_RasCalc.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.box_RasCalc.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.box_RasCalc.setFrameShadow(QtWidgets.QFrame.Raised)
        self.box_RasCalc.setObjectName("box_RasCalc")
        self.PatchEdges = QtWidgets.QWidget()
        self.PatchEdges.setGeometry(QtCore.QRect(0, 0, 469, 119))
        self.PatchEdges.setObjectName("PatchEdges")
        self.helpText = QtWidgets.QTextEdit(self.PatchEdges)
        self.helpText.setGeometry(QtCore.QRect(290, 0, 171, 91))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpText.sizePolicy().hasHeightForWidth())
        self.helpText.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.helpText.setFont(font)
        self.helpText.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.helpText.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.helpText.setLineWidth(0)
        self.helpText.setMidLineWidth(0)
        self.helpText.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.helpText.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.helpText.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.helpText.setReadOnly(True)
        self.helpText.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.helpText.setObjectName("helpText")
        self.horizontalLayoutWidget_3 = QtWidgets.QWidget(self.PatchEdges)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(10, 30, 160, 31))
        self.horizontalLayoutWidget_3.setObjectName("horizontalLayoutWidget_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.sp_EdgeMult = QtWidgets.QSpinBox(self.horizontalLayoutWidget_3)
        self.sp_EdgeMult.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.sp_EdgeMult.setMinimum(1)
        self.sp_EdgeMult.setProperty("value", 1)
        self.sp_EdgeMult.setObjectName("sp_EdgeMult")
        self.horizontalLayout_3.addWidget(self.sp_EdgeMult)
        self.label_3 = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.CellsizeLine = QtWidgets.QLineEdit(self.horizontalLayoutWidget_3)
        self.CellsizeLine.setAlignment(QtCore.Qt.AlignCenter)
        self.CellsizeLine.setReadOnly(True)
        self.CellsizeLine.setObjectName("CellsizeLine")
        self.horizontalLayout_3.addWidget(self.CellsizeLine)
        self.label_4 = QtWidgets.QLabel(self.PatchEdges)
        self.label_4.setGeometry(QtCore.QRect(10, 10, 81, 16))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label_4.setTextFormat(QtCore.Qt.AutoText)
        self.label_4.setWordWrap(False)
        self.label_4.setObjectName("label_4")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Modify_Res/icons/img_EdgeExtract.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.box_RasCalc.addItem(self.PatchEdges, icon1, "")
        self.IsoMaxMinPatch = QtWidgets.QWidget()
        self.IsoMaxMinPatch.setGeometry(QtCore.QRect(0, 0, 98, 28))
        self.IsoMaxMinPatch.setObjectName("IsoMaxMinPatch")
        self.helpText_2 = QtWidgets.QTextEdit(self.IsoMaxMinPatch)
        self.helpText_2.setGeometry(QtCore.QRect(290, 0, 171, 91))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpText_2.sizePolicy().hasHeightForWidth())
        self.helpText_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.helpText_2.setFont(font)
        self.helpText_2.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.helpText_2.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.helpText_2.setLineWidth(0)
        self.helpText_2.setMidLineWidth(0)
        self.helpText_2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.helpText_2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.helpText_2.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.helpText_2.setReadOnly(True)
        self.helpText_2.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.helpText_2.setObjectName("helpText_2")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.IsoMaxMinPatch)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 0, 141, 91))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.rb_MaxMin1 = QtWidgets.QRadioButton(self.verticalLayoutWidget)
        self.rb_MaxMin1.setChecked(False)
        self.rb_MaxMin1.setObjectName("rb_MaxMin1")
        self.verticalLayout.addWidget(self.rb_MaxMin1)
        self.rb_MaxMin2 = QtWidgets.QRadioButton(self.verticalLayoutWidget)
        self.rb_MaxMin2.setChecked(True)
        self.rb_MaxMin2.setObjectName("rb_MaxMin2")
        self.verticalLayout.addWidget(self.rb_MaxMin2)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/Modify_Res/icons/img_MaxMin.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.box_RasCalc.addItem(self.IsoMaxMinPatch, icon2, "")
        self.IncDecLand = QtWidgets.QWidget()
        self.IncDecLand.setGeometry(QtCore.QRect(0, 0, 98, 28))
        self.IncDecLand.setObjectName("IncDecLand")
        self.helpText_3 = QtWidgets.QTextEdit(self.IncDecLand)
        self.helpText_3.setGeometry(QtCore.QRect(290, 0, 171, 91))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpText_3.sizePolicy().hasHeightForWidth())
        self.helpText_3.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.helpText_3.setFont(font)
        self.helpText_3.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.helpText_3.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.helpText_3.setLineWidth(0)
        self.helpText_3.setMidLineWidth(0)
        self.helpText_3.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.helpText_3.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.helpText_3.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.helpText_3.setReadOnly(True)
        self.helpText_3.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.helpText_3.setObjectName("helpText_3")
        self.horizontalLayoutWidget_4 = QtWidgets.QWidget(self.IncDecLand)
        self.horizontalLayoutWidget_4.setGeometry(QtCore.QRect(19, 9, 231, 81))
        self.horizontalLayoutWidget_4.setObjectName("horizontalLayoutWidget_4")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.sp_IncDecAm = QtWidgets.QSpinBox(self.horizontalLayoutWidget_4)
        self.sp_IncDecAm.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.sp_IncDecAm.setPrefix("")
        self.sp_IncDecAm.setMinimum(1)
        self.sp_IncDecAm.setProperty("value", 1)
        self.sp_IncDecAm.setObjectName("sp_IncDecAm")
        self.horizontalLayout_4.addWidget(self.sp_IncDecAm)
        self.cb_IncDec = QtWidgets.QComboBox(self.horizontalLayoutWidget_4)
        self.cb_IncDec.setObjectName("cb_IncDec")
        self.cb_IncDec.addItem("")
        self.cb_IncDec.addItem("")
        self.horizontalLayout_4.addWidget(self.cb_IncDec)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/Modify_Res/icons/img_IncDec.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.box_RasCalc.addItem(self.IncDecLand, icon3, "")
        self.fillHoles = QtWidgets.QWidget()
        self.fillHoles.setGeometry(QtCore.QRect(0, 0, 98, 28))
        self.fillHoles.setObjectName("fillHoles")
        self.helpText_4 = QtWidgets.QTextEdit(self.fillHoles)
        self.helpText_4.setGeometry(QtCore.QRect(290, 0, 171, 91))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpText_4.sizePolicy().hasHeightForWidth())
        self.helpText_4.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.helpText_4.setFont(font)
        self.helpText_4.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.helpText_4.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.helpText_4.setLineWidth(0)
        self.helpText_4.setMidLineWidth(0)
        self.helpText_4.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.helpText_4.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.helpText_4.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.helpText_4.setReadOnly(True)
        self.helpText_4.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.helpText_4.setObjectName("helpText_4")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/Modify_Res/icons/img_closeHole.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.box_RasCalc.addItem(self.fillHoles, icon4, "")
        self.cleanPixel = QtWidgets.QWidget()
        self.cleanPixel.setGeometry(QtCore.QRect(0, 0, 98, 28))
        self.cleanPixel.setObjectName("cleanPixel")
        self.helpText_5 = QtWidgets.QTextEdit(self.cleanPixel)
        self.helpText_5.setGeometry(QtCore.QRect(290, 0, 171, 91))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpText_5.sizePolicy().hasHeightForWidth())
        self.helpText_5.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.helpText_5.setFont(font)
        self.helpText_5.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.helpText_5.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.helpText_5.setLineWidth(0)
        self.helpText_5.setMidLineWidth(0)
        self.helpText_5.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.helpText_5.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.helpText_5.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.helpText_5.setReadOnly(True)
        self.helpText_5.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.helpText_5.setObjectName("helpText_5")
        self.sp_CleanIter = QtWidgets.QSpinBox(self.cleanPixel)
        self.sp_CleanIter.setGeometry(QtCore.QRect(10, 30, 56, 25))
        self.sp_CleanIter.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.sp_CleanIter.setPrefix("")
        self.sp_CleanIter.setMinimum(1)
        self.sp_CleanIter.setProperty("value", 1)
        self.sp_CleanIter.setObjectName("sp_CleanIter")
        self.label_2 = QtWidgets.QLabel(self.cleanPixel)
        self.label_2.setGeometry(QtCore.QRect(80, 30, 151, 21))
        self.label_2.setObjectName("label_2")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/Modify_Res/icons/img_CleanRas.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.box_RasCalc.addItem(self.cleanPixel, icon5, "")
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(LandMod)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(10, 40, 471, 31))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.where2Save = QtWidgets.QLineEdit(self.horizontalLayoutWidget_2)
        self.where2Save.setObjectName("where2Save")
        self.horizontalLayout_2.addWidget(self.where2Save)
        self.btn_Save = QtWidgets.QToolButton(self.horizontalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_Save.sizePolicy().hasHeightForWidth())
        self.btn_Save.setSizePolicy(sizePolicy)
        self.btn_Save.setObjectName("btn_Save")
        self.horizontalLayout_2.addWidget(self.btn_Save)
        self.horizontalLayoutWidget_5 = QtWidgets.QWidget(LandMod)
        self.horizontalLayoutWidget_5.setGeometry(QtCore.QRect(10, 370, 471, 31))
        self.horizontalLayoutWidget_5.setObjectName("horizontalLayoutWidget_5")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_5)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.addToToc = QtWidgets.QCheckBox(self.horizontalLayoutWidget_5)
        self.addToToc.setChecked(True)
        self.addToToc.setObjectName("addToToc")
        self.horizontalLayout_5.addWidget(self.addToToc)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.horizontalLayoutWidget_5)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_5.addWidget(self.buttonBox)
        self.line_2 = QtWidgets.QFrame(LandMod)
        self.line_2.setGeometry(QtCore.QRect(10, 360, 471, 16))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")

        self.retranslateUi(LandMod)
        self.box_RasCalc.setCurrentIndex(0)
        self.box_RasCalc.layout().setSpacing(6)
        self.buttonBox.accepted.connect(LandMod.accept)
        self.buttonBox.rejected.connect(LandMod.reject)
        QtCore.QMetaObject.connectSlotsByName(LandMod)

    def retranslateUi(self, LandMod):
        _translate = QtCore.QCoreApplication.translate
        LandMod.setWindowTitle(_translate("LandMod", "Landscape Modifier"))
        self.label.setText(_translate("LandMod", "Class:"))
        self.helpText.setHtml(_translate("LandMod", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Extracts edges from each patch of the given class. Edge width can be specified by multiplying the cellsize.</span></p></body></html>"))
        self.label_3.setText(_translate("LandMod", "x"))
        self.label_4.setText(_translate("LandMod", "Edge width"))
        self.box_RasCalc.setItemText(self.box_RasCalc.indexOf(self.PatchEdges), _translate("LandMod", "Extract landscape patch edges"))
        self.helpText_2.setHtml(_translate("LandMod", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Returns a raster with the greatest/smallest identified landcover patch. If multiple patches fullfill this criteria, than all of them are returned.</span></p></body></html>"))
        self.rb_MaxMin1.setText(_translate("LandMod", "Smallest"))
        self.rb_MaxMin2.setText(_translate("LandMod", "Greatest"))
        self.box_RasCalc.setItemText(self.box_RasCalc.indexOf(self.IsoMaxMinPatch), _translate("LandMod", "Isolate smallest or greatest patch"))
        self.helpText_3.setHtml(_translate("LandMod", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Let the user increase or decrease all landscape patches of a given class. The amount can be specified in the Spinbox.</span></p></body></html>"))
        self.sp_IncDecAm.setSuffix(_translate("LandMod", " x"))
        self.cb_IncDec.setItemText(0, _translate("LandMod", "Increase"))
        self.cb_IncDec.setItemText(1, _translate("LandMod", "Decrease"))
        self.box_RasCalc.setItemText(self.box_RasCalc.indexOf(self.IncDecLand), _translate("LandMod", "Increase or decrease landscape patches"))
        self.helpText_4.setHtml(_translate("LandMod", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Closes holes (inner rings) in all patches of the specified landcover class</span></p></body></html>"))
        self.box_RasCalc.setItemText(self.box_RasCalc.indexOf(self.fillHoles), _translate("LandMod", "Fill Holes inside landscape patches"))
        self.helpText_5.setHtml(_translate("LandMod", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Returns a raster with all pixels smaller than the structure removed. User can determine how many iterations should be performed.</span></p></body></html>"))
        self.sp_CleanIter.setSuffix(_translate("LandMod", " x"))
        self.label_2.setText(_translate("LandMod", "Taxicab structure"))
        self.box_RasCalc.setItemText(self.box_RasCalc.indexOf(self.cleanPixel), _translate("LandMod", "Cleans landscape of small border pixels"))
        self.where2Save.setPlaceholderText(_translate("LandMod", "Choose output or leave blank for creating a temp file"))
        self.btn_Save.setText(_translate("LandMod", "..."))
        self.addToToc.setText(_translate("LandMod", "Add result to QGis afterwards"))

from .res_PatchModify_rc import *
