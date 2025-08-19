# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_cnt.ui'
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
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_CNTDialog(object):
    def setupUi(self, dialog_cnt):
        if not dialog_cnt.objectName():
            dialog_cnt.setObjectName(u"dialog_cnt")
        dialog_cnt.setModal(True)
        self.verticalLayout = QVBoxLayout(dialog_cnt)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(dialog_cnt)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_type = QLabel(self.widget)
        self.label_type.setObjectName(u"label_type")
        self.label_type.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_type, 0, 0, 1, 1)

        self.combo_type = QComboBox(self.widget)
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.setObjectName(u"combo_type")

        self.gridLayout.addWidget(self.combo_type, 0, 1, 1, 1)

        self.label_vecx = QLabel(self.widget)
        self.label_vecx.setObjectName(u"label_vecx")
        self.label_vecx.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_vecx, 1, 0, 1, 1)

        self.spin_vec_x = QDoubleSpinBox(self.widget)
        self.spin_vec_x.setObjectName(u"spin_vec_x")
        self.spin_vec_x.setMinimum(-9999.000000000000000)
        self.spin_vec_x.setMaximum(9999.000000000000000)
        self.spin_vec_x.setValue(1.000000000000000)
        self.spin_vec_x.setSingleStep(0.100000000000000)

        self.gridLayout.addWidget(self.spin_vec_x, 1, 1, 1, 1)

        self.label_vecy = QLabel(self.widget)
        self.label_vecy.setObjectName(u"label_vecy")
        self.label_vecy.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_vecy, 2, 0, 1, 1)

        self.spin_vec_y = QDoubleSpinBox(self.widget)
        self.spin_vec_y.setObjectName(u"spin_vec_y")
        self.spin_vec_y.setMinimum(-9999.000000000000000)
        self.spin_vec_y.setMaximum(9999.000000000000000)
        self.spin_vec_y.setValue(0.000000000000000)
        self.spin_vec_y.setSingleStep(0.100000000000000)

        self.gridLayout.addWidget(self.spin_vec_y, 2, 1, 1, 1)


        self.verticalLayout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox(dialog_cnt)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dialog_cnt)
        self.buttonBox.accepted.connect(dialog_cnt.accept)
        self.buttonBox.rejected.connect(dialog_cnt.reject)

        QMetaObject.connectSlotsByName(dialog_cnt)
    # setupUi

    def retranslateUi(self, dialog_cnt):
        dialog_cnt.setWindowTitle(QCoreApplication.translate("CNTDialog", u"Carbon Nanotube Settings", None))
        self.label_type.setText(QCoreApplication.translate("CNTDialog", u"CNT Type:", None))
        self.combo_type.setItemText(0, QCoreApplication.translate("CNTDialog", u"Zigzag", None))
        self.combo_type.setItemText(1, QCoreApplication.translate("CNTDialog", u"Armchair", None))
        self.combo_type.setItemText(2, QCoreApplication.translate("CNTDialog", u"Custom", None))

        self.label_vecx.setText(QCoreApplication.translate("CNTDialog", u"Wrapping Vector X:", None))
        self.label_vecy.setText(QCoreApplication.translate("CNTDialog", u"Wrapping Vector Y:", None))
    # retranslateUi

