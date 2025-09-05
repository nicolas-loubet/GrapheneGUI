# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'atom_type.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QGridLayout, QLabel,
    QLineEdit, QSizePolicy, QVBoxLayout, QWidget)

class Ui_AtomTypeDialog(object):
    def setupUi(self, AtomTypeDialog):
        if not AtomTypeDialog.objectName():
            AtomTypeDialog.setObjectName(u"AtomTypeDialog")
        AtomTypeDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(AtomTypeDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(AtomTypeDialog)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_name = QLabel(self.widget)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_name, 0, 0, 1, 1)

        self.le_name = QLineEdit(self.widget)
        self.le_name.setObjectName(u"le_name")

        self.gridLayout.addWidget(self.le_name, 0, 1, 1, 1)

        self.label_epsilon_cc = QLabel(self.widget)
        self.label_epsilon_cc.setObjectName(u"label_epsilon_cc")
        self.label_epsilon_cc.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_epsilon_cc, 1, 0, 1, 1)

        self.sb_epsilon_cc = QDoubleSpinBox(self.widget)
        self.sb_epsilon_cc.setObjectName(u"sb_epsilon_cc")
        self.sb_epsilon_cc.setDecimals(6)
        self.sb_epsilon_cc.setMinimum(0.000000000000000)
        self.sb_epsilon_cc.setMaximum(1000000.000000000000000)
        self.sb_epsilon_cc.setSingleStep(0.000001000000000)
        self.sb_epsilon_cc.setValue(0.359824000000000)

        self.gridLayout.addWidget(self.sb_epsilon_cc, 1, 1, 1, 1)

        self.label_sigma_cc = QLabel(self.widget)
        self.label_sigma_cc.setObjectName(u"label_sigma_cc")
        self.label_sigma_cc.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_sigma_cc, 2, 0, 1, 1)

        self.sb_sigma_cc = QDoubleSpinBox(self.widget)
        self.sb_sigma_cc.setObjectName(u"sb_sigma_cc")
        self.sb_sigma_cc.setDecimals(6)
        self.sb_sigma_cc.setMinimum(0.000000000000000)
        self.sb_sigma_cc.setMaximum(1000000.000000000000000)
        self.sb_sigma_cc.setSingleStep(0.000001000000000)
        self.sb_sigma_cc.setValue(0.339967000000000)

        self.gridLayout.addWidget(self.sb_sigma_cc, 2, 1, 1, 1)

        self.label_water_model = QLabel(self.widget)
        self.label_water_model.setObjectName(u"label_water_model")
        self.label_water_model.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_water_model, 3, 0, 1, 1)

        self.cb_water = QComboBox(self.widget)
        self.cb_water.addItem("")
        self.cb_water.addItem("")
        self.cb_water.addItem("")
        self.cb_water.addItem("")
        self.cb_water.addItem("")
        self.cb_water.addItem("")
        self.cb_water.addItem("")
        self.cb_water.setObjectName(u"cb_water")

        self.gridLayout.addWidget(self.cb_water, 3, 1, 1, 1)

        self.label_epsilon_oo = QLabel(self.widget)
        self.label_epsilon_oo.setObjectName(u"label_epsilon_oo")
        self.label_epsilon_oo.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_epsilon_oo, 4, 0, 1, 1)

        self.lbl_epsilon_oo = QLabel(self.widget)
        self.lbl_epsilon_oo.setObjectName(u"lbl_epsilon_oo")

        self.gridLayout.addWidget(self.lbl_epsilon_oo, 4, 1, 1, 1)

        self.label_sigma_oo = QLabel(self.widget)
        self.label_sigma_oo.setObjectName(u"label_sigma_oo")
        self.label_sigma_oo.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_sigma_oo, 5, 0, 1, 1)

        self.lbl_sigma_oo = QLabel(self.widget)
        self.lbl_sigma_oo.setObjectName(u"lbl_sigma_oo")

        self.gridLayout.addWidget(self.lbl_sigma_oo, 5, 1, 1, 1)

        self.label_epsilon_co = QLabel(self.widget)
        self.label_epsilon_co.setObjectName(u"label_epsilon_co")
        self.label_epsilon_co.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_epsilon_co, 6, 0, 1, 1)

        self.lbl_epsilon_co = QLabel(self.widget)
        self.lbl_epsilon_co.setObjectName(u"lbl_epsilon_co")

        self.gridLayout.addWidget(self.lbl_epsilon_co, 6, 1, 1, 1)

        self.label_sigma_co = QLabel(self.widget)
        self.label_sigma_co.setObjectName(u"label_sigma_co")
        self.label_sigma_co.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_sigma_co, 7, 0, 1, 1)

        self.lbl_sigma_co = QLabel(self.widget)
        self.lbl_sigma_co.setObjectName(u"lbl_sigma_co")

        self.gridLayout.addWidget(self.lbl_sigma_co, 7, 1, 1, 1)

        self.label_percent_epsilon = QLabel(self.widget)
        self.label_percent_epsilon.setObjectName(u"label_percent_epsilon")
        self.label_percent_epsilon.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_percent_epsilon, 8, 0, 1, 1)

        self.sb_percent_epsilon = QDoubleSpinBox(self.widget)
        self.sb_percent_epsilon.setObjectName(u"sb_percent_epsilon")
        self.sb_percent_epsilon.setDecimals(1)
        self.sb_percent_epsilon.setMinimum(0.000000000000000)
        self.sb_percent_epsilon.setMaximum(1000000.000000000000000)
        self.sb_percent_epsilon.setSingleStep(1.000000000000000)
        self.sb_percent_epsilon.setValue(100.000000000000000)

        self.gridLayout.addWidget(self.sb_percent_epsilon, 8, 1, 1, 1)

        self.label_percent_sigma = QLabel(self.widget)
        self.label_percent_sigma.setObjectName(u"label_percent_sigma")
        self.label_percent_sigma.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_percent_sigma, 9, 0, 1, 1)

        self.sb_percent_sigma = QDoubleSpinBox(self.widget)
        self.sb_percent_sigma.setObjectName(u"sb_percent_sigma")
        self.sb_percent_sigma.setDecimals(1)
        self.sb_percent_sigma.setMinimum(0.000000000000000)
        self.sb_percent_sigma.setMaximum(1000000.000000000000000)
        self.sb_percent_sigma.setSingleStep(1.000000000000000)
        self.sb_percent_sigma.setValue(100.000000000000000)

        self.gridLayout.addWidget(self.sb_percent_sigma, 9, 1, 1, 1)


        self.verticalLayout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox(AtomTypeDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(AtomTypeDialog)
        self.buttonBox.accepted.connect(AtomTypeDialog.accept)
        self.buttonBox.rejected.connect(AtomTypeDialog.reject)

        QMetaObject.connectSlotsByName(AtomTypeDialog)
    # setupUi

    def retranslateUi(self, AtomTypeDialog):
        AtomTypeDialog.setWindowTitle(QCoreApplication.translate("AtomTypeDialog", u"Add New Carbon Type", None))
        self.label_name.setText(QCoreApplication.translate("AtomTypeDialog", u"Type Name:", None))
        self.label_epsilon_cc.setText(QCoreApplication.translate("AtomTypeDialog", u"Epsilon CC (kJ/mol):", None))
        self.label_sigma_cc.setText(QCoreApplication.translate("AtomTypeDialog", u"Sigma CC (\u00c5):", None))
        self.label_water_model.setText(QCoreApplication.translate("AtomTypeDialog", u"Water Model:", None))
        self.cb_water.setItemText(0, QCoreApplication.translate("AtomTypeDialog", u"TIP3P", None))
        self.cb_water.setItemText(1, QCoreApplication.translate("AtomTypeDialog", u"TIP4P", None))
        self.cb_water.setItemText(2, QCoreApplication.translate("AtomTypeDialog", u"TIP4P/2005", None))
        self.cb_water.setItemText(3, QCoreApplication.translate("AtomTypeDialog", u"TIP5P", None))
        self.cb_water.setItemText(4, QCoreApplication.translate("AtomTypeDialog", u"TIP5P-2018", None))
        self.cb_water.setItemText(5, QCoreApplication.translate("AtomTypeDialog", u"SPC", None))
        self.cb_water.setItemText(6, QCoreApplication.translate("AtomTypeDialog", u"SPC/E", None))

        self.label_epsilon_oo.setText(QCoreApplication.translate("AtomTypeDialog", u"Epsilon OO:", None))
        self.lbl_epsilon_oo.setText(QCoreApplication.translate("AtomTypeDialog", u"0.636400", None))
        self.label_sigma_oo.setText(QCoreApplication.translate("AtomTypeDialog", u"Sigma OO:", None))
        self.lbl_sigma_oo.setText(QCoreApplication.translate("AtomTypeDialog", u"0.315070", None))
        self.label_epsilon_co.setText(QCoreApplication.translate("AtomTypeDialog", u"Calculated Epsilon CO:", None))
        self.lbl_epsilon_co.setText(QCoreApplication.translate("AtomTypeDialog", u"0.000000", None))
        self.label_sigma_co.setText(QCoreApplication.translate("AtomTypeDialog", u"Calculated Sigma CO:", None))
        self.lbl_sigma_co.setText(QCoreApplication.translate("AtomTypeDialog", u"0.000000", None))
        self.label_percent_epsilon.setText(QCoreApplication.translate("AtomTypeDialog", u"% Modification Epsilon CO:", None))
        self.sb_percent_epsilon.setSuffix(QCoreApplication.translate("AtomTypeDialog", u"%", None))
        self.label_percent_sigma.setText(QCoreApplication.translate("AtomTypeDialog", u"% Modification Sigma CO:", None))
        self.sb_percent_sigma.setSuffix(QCoreApplication.translate("AtomTypeDialog", u"%", None))
    # retranslateUi

