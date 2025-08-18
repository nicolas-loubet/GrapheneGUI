# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGraphicsView,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QToolBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1000, 700)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_1 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_1.setObjectName(u"verticalLayout_1")
        self.topToolBar = QToolBar(self.centralwidget)
        self.topToolBar.setObjectName(u"topToolBar")
        self.topToolBar.setIconSize(QSize(48, 40))
        self.btnCreate = QPushButton(self.topToolBar)
        self.btnCreate.setObjectName(u"btnCreate")
        self.btnCreate.setMinimumSize(QSize(100, 40))
        icon = QIcon()
        icon.addFile(u":/icons/img/svg/create.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnCreate.setIcon(icon)
        self.btnCreate.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnCreate)
        self.comboDrawings = QComboBox(self.topToolBar)
        self.comboDrawings.setObjectName(u"comboDrawings")
        self.comboDrawings.setMinimumSize(QSize(150, 40))
        self.comboDrawings.setEnabled(False)
        self.topToolBar.addWidget(self.comboDrawings)
        self.btnDuplicate = QPushButton(self.topToolBar)
        self.btnDuplicate.setObjectName(u"btnDuplicate")
        self.btnDuplicate.setMinimumSize(QSize(100, 40))
        icon1 = QIcon()
        icon1.addFile(u":/icons/img/svg/duplicate.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnDuplicate.setIcon(icon1)
        self.btnDuplicate.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnDuplicate)
        self.btnDelete = QPushButton(self.topToolBar)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setMinimumSize(QSize(100, 40))
        icon2 = QIcon()
        icon2.addFile(u":/icons/img/svg/delete.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnDelete.setIcon(icon2)
        self.btnDelete.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnDelete)
        self.btnImport = QPushButton(self.topToolBar)
        self.btnImport.setObjectName(u"btnImport")
        self.btnImport.setMinimumSize(QSize(100, 40))
        icon3 = QIcon()
        icon3.addFile(u":/icons/img/svg/import.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnImport.setIcon(icon3)
        self.btnImport.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnImport)
        self.btnExport = QPushButton(self.topToolBar)
        self.btnExport.setObjectName(u"btnExport")
        self.btnExport.setMinimumSize(QSize(100, 40))
        icon4 = QIcon()
        icon4.addFile(u":/icons/img/svg/export.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnExport.setIcon(icon4)
        self.btnExport.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnExport)
        self.btnCNT = QPushButton(self.topToolBar)
        self.btnCNT.setObjectName(u"btnCNT")
        self.btnCNT.setMinimumSize(QSize(100, 40))
        icon5 = QIcon()
        icon5.addFile(u":/icons/img/svg/cnt.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnCNT.setIcon(icon5)
        self.btnCNT.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnCNT)
        self.btnTheme = QPushButton(self.topToolBar)
        self.btnTheme.setObjectName(u"btnTheme")
        self.btnTheme.setMinimumSize(QSize(100, 40))
        icon6 = QIcon()
        icon6.addFile(u":/icons/img/svg/dark_light_mode.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnTheme.setIcon(icon6)
        self.btnTheme.setIconSize(QSize(25, 25))
        self.topToolBar.addWidget(self.btnTheme)

        self.verticalLayout_1.addWidget(self.topToolBar)

        self.drawingArea = QWidget(self.centralwidget)
        self.drawingArea.setObjectName(u"drawingArea")
        self.gridLayoutCentral = QGridLayout(self.drawingArea)
        self.gridLayoutCentral.setSpacing(0)
        self.gridLayoutCentral.setObjectName(u"gridLayoutCentral")
        self.gridLayoutCentral.setContentsMargins(0, 0, 0, 0)
        self.cornerSpacer = QSpacerItem(40, 40, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayoutCentral.addItem(self.cornerSpacer, 0, 0, 1, 1)

        self.topRuler = QWidget(self.drawingArea)
        self.topRuler.setObjectName(u"topRuler")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.topRuler.sizePolicy().hasHeightForWidth())
        self.topRuler.setSizePolicy(sizePolicy)
        self.topRuler.setMinimumSize(QSize(0, 40))
        self.topRuler.setStyleSheet(u"background-color: #f0f0f0; border: 1px solid #ccc;")

        self.gridLayoutCentral.addWidget(self.topRuler, 0, 1, 1, 1)

        self.leftRuler = QWidget(self.drawingArea)
        self.leftRuler.setObjectName(u"leftRuler")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leftRuler.sizePolicy().hasHeightForWidth())
        self.leftRuler.setSizePolicy(sizePolicy1)
        self.leftRuler.setMinimumSize(QSize(40, 0))
        self.leftRuler.setStyleSheet(u"background-color: #f0f0f0; border: 1px solid #ccc;")

        self.gridLayoutCentral.addWidget(self.leftRuler, 1, 0, 1, 1)

        self.graphicsView = QGraphicsView(self.drawingArea)
        self.graphicsView.setObjectName(u"graphicsView")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy2)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.gridLayoutCentral.addWidget(self.graphicsView, 1, 1, 1, 1)


        self.verticalLayout_1.addWidget(self.drawingArea)

        self.bottomBar = QWidget(self.centralwidget)
        self.bottomBar.setObjectName(u"bottomBar")
        self.hLayoutBottom = QHBoxLayout(self.bottomBar)
        self.hLayoutBottom.setObjectName(u"hLayoutBottom")
        self.hLayoutBottom.setContentsMargins(0, 0, 0, 0)
        self.labelOxidation = QLabel(self.bottomBar)
        self.labelOxidation.setObjectName(u"labelOxidation")

        self.hLayoutBottom.addWidget(self.labelOxidation)

        self.btnReduceAll = QPushButton(self.bottomBar)
        self.btnReduceAll.setObjectName(u"btnReduceAll")
        icon7 = QIcon()
        icon7.addFile(u":/icons/img/svg/reduce.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnReduceAll.setIcon(icon7)
        self.btnReduceAll.setMinimumSize(QSize(100, 40))
        self.btnReduceAll.setIconSize(QSize(25, 25))

        self.hLayoutBottom.addWidget(self.btnReduceAll)

        self.btnChangeProb = QPushButton(self.bottomBar)
        self.btnChangeProb.setObjectName(u"btnChangeProb")
        icon8 = QIcon()
        icon8.addFile(u":/icons/img/svg/prob.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnChangeProb.setIcon(icon8)
        self.btnChangeProb.setMinimumSize(QSize(130, 40))
        self.btnChangeProb.setIconSize(QSize(25, 25))

        self.hLayoutBottom.addWidget(self.btnChangeProb)

        self.line1 = QFrame(self.bottomBar)
        self.line1.setObjectName(u"line1")
        self.line1.setFrameShape(QFrame.Shape.VLine)
        self.line1.setFrameShadow(QFrame.Shadow.Sunken)

        self.hLayoutBottom.addWidget(self.line1)

        self.labelRandom = QLabel(self.bottomBar)
        self.labelRandom.setObjectName(u"labelRandom")

        self.hLayoutBottom.addWidget(self.labelRandom)

        self.spinRandom = QSpinBox(self.bottomBar)
        self.spinRandom.setObjectName(u"spinRandom")
        self.spinRandom.setMinimumSize(QSize(60, 40))
        self.spinRandom.setMinimum(0)
        self.spinRandom.setMaximum(100)
        self.spinRandom.setSingleStep(5)

        self.hLayoutBottom.addWidget(self.spinRandom)

        self.line2 = QFrame(self.bottomBar)
        self.line2.setObjectName(u"line2")
        self.line2.setFrameShape(QFrame.Shape.VLine)
        self.line2.setFrameShadow(QFrame.Shadow.Sunken)

        self.hLayoutBottom.addWidget(self.line2)

        self.labelVMD = QLabel(self.bottomBar)
        self.labelVMD.setObjectName(u"labelVMD")

        self.hLayoutBottom.addWidget(self.labelVMD)

        self.entryVMD = QLineEdit(self.bottomBar)
        self.entryVMD.setObjectName(u"entryVMD")
        self.entryVMD.setMinimumSize(QSize(120, 40))

        self.hLayoutBottom.addWidget(self.entryVMD)

        self.line3 = QFrame(self.bottomBar)
        self.line3.setObjectName(u"line3")
        self.line3.setFrameShape(QFrame.Shape.VLine)
        self.line3.setFrameShadow(QFrame.Shadow.Sunken)

        self.hLayoutBottom.addWidget(self.line3)

        self.labelManual = QLabel(self.bottomBar)
        self.labelManual.setObjectName(u"labelManual")

        self.hLayoutBottom.addWidget(self.labelManual)

        self.btnAddOH = QPushButton(self.bottomBar)
        self.btnAddOH.setObjectName(u"btnAddOH")
        self.btnAddOH.setCheckable(True)
        self.btnAddOH.setMinimumSize(QSize(60, 40))

        self.hLayoutBottom.addWidget(self.btnAddOH)

        self.btnAddO = QPushButton(self.bottomBar)
        self.btnAddO.setObjectName(u"btnAddO")
        self.btnAddO.setCheckable(True)
        self.btnAddO.setMinimumSize(QSize(60, 40))

        self.hLayoutBottom.addWidget(self.btnAddO)

        self.btnRemoveOx = QPushButton(self.bottomBar)
        self.btnRemoveOx.setObjectName(u"btnRemoveOx")
        self.btnRemoveOx.setCheckable(True)
        icon9 = QIcon()
        icon9.addFile(u":/icons/img/svg/remove_one.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnRemoveOx.setIcon(icon9)
        self.btnRemoveOx.setMinimumSize(QSize(110, 40))
        self.btnRemoveOx.setIconSize(QSize(25, 25))

        self.hLayoutBottom.addWidget(self.btnRemoveOx)

        self.line4 = QFrame(self.bottomBar)
        self.line4.setObjectName(u"line4")
        self.line4.setFrameShape(QFrame.Shape.VLine)
        self.line4.setFrameShadow(QFrame.Shadow.Sunken)

        self.hLayoutBottom.addWidget(self.line4)

        self.labelWhere = QLabel(self.bottomBar)
        self.labelWhere.setObjectName(u"labelWhere")

        self.hLayoutBottom.addWidget(self.labelWhere)

        self.radioGroupWhere = QWidget(self.bottomBar)
        self.radioGroupWhere.setObjectName(u"radioGroupWhere")
        self.hLayoutWhere = QHBoxLayout(self.radioGroupWhere)
        self.hLayoutWhere.setObjectName(u"hLayoutWhere")
        self.hLayoutWhere.setContentsMargins(0, 0, 0, 0)
        self.radioZpm = QRadioButton(self.radioGroupWhere)
        self.radioZpm.setObjectName(u"radioZpm")

        self.hLayoutWhere.addWidget(self.radioZpm)

        self.radioZp = QRadioButton(self.radioGroupWhere)
        self.radioZp.setObjectName(u"radioZp")

        self.hLayoutWhere.addWidget(self.radioZp)

        self.radioZm = QRadioButton(self.radioGroupWhere)
        self.radioZm.setObjectName(u"radioZm")

        self.hLayoutWhere.addWidget(self.radioZm)


        self.hLayoutBottom.addWidget(self.radioGroupWhere)


        self.verticalLayout_1.addWidget(self.bottomBar)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Graphene GUI", None))
        self.btnCreate.setText(QCoreApplication.translate("MainWindow", u"Create", None))
        self.btnDuplicate.setText(QCoreApplication.translate("MainWindow", u"Duplicate", None))
        self.btnDelete.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btnImport.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.btnExport.setText(QCoreApplication.translate("MainWindow", u"Export", None))
        self.btnCNT.setText(QCoreApplication.translate("MainWindow", u"CNT", None))
        self.btnTheme.setText(QCoreApplication.translate("MainWindow", u"Light/Dark", None))
        self.labelOxidation.setText(QCoreApplication.translate("MainWindow", u"Oxidation:", None))
        self.btnReduceAll.setText(QCoreApplication.translate("MainWindow", u"Reduce All", None))
        self.btnChangeProb.setText(QCoreApplication.translate("MainWindow", u"Change Prob.", None))
        self.labelRandom.setText(QCoreApplication.translate("MainWindow", u"Random", None))
        self.spinRandom.setSuffix(QCoreApplication.translate("MainWindow", u"%", None))
        self.labelVMD.setText(QCoreApplication.translate("MainWindow", u"VMD Selection:", None))
        self.labelManual.setText(QCoreApplication.translate("MainWindow", u"Manual", None))
        self.btnAddOH.setText(QCoreApplication.translate("MainWindow", u"Add OH", None))
        self.btnAddO.setText(QCoreApplication.translate("MainWindow", u"Add O", None))
        self.btnRemoveOx.setText(QCoreApplication.translate("MainWindow", u"Remove Ox.", None))
        self.labelWhere.setText(QCoreApplication.translate("MainWindow", u"Where:", None))
        self.radioZpm.setText(QCoreApplication.translate("MainWindow", u"z\u00b1", None))
        self.radioZp.setText(QCoreApplication.translate("MainWindow", u"z+", None))
        self.radioZm.setText(QCoreApplication.translate("MainWindow", u"z-", None))
    # retranslateUi

