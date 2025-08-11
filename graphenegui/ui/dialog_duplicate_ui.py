# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_duplicate.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QGridLayout, QLabel, QRadioButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogDuplicate(object):
    def setupUi(self, dialog_duplicate):
        if not dialog_duplicate.objectName():
            dialog_duplicate.setObjectName(u"dialog_duplicate")
        dialog_duplicate.setModal(True)
        self.verticalLayout = QVBoxLayout(dialog_duplicate)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(dialog_duplicate)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.duplicate_label = QLabel(self.widget)
        self.duplicate_label.setObjectName(u"duplicate_label")

        self.verticalLayout_2.addWidget(self.duplicate_label)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.radio_btn_relative_coords = QRadioButton(self.widget)
        self.radio_btn_relative_coords.setObjectName(u"radio_btn_relative_coords")
        self.radio_btn_relative_coords.setChecked(True)

        self.verticalLayout_3.addWidget(self.radio_btn_relative_coords)

        self.radio_btn_absolute_pos = QRadioButton(self.widget)
        self.radio_btn_absolute_pos.setObjectName(u"radio_btn_absolute_pos")

        self.verticalLayout_3.addWidget(self.radio_btn_absolute_pos)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.spin_duplicate_x = QDoubleSpinBox(self.widget)
        self.spin_duplicate_x.setObjectName(u"spin_duplicate_x")
        self.spin_duplicate_x.setMinimum(-1000.000000000000000)
        self.spin_duplicate_x.setMaximum(1000.000000000000000)
        self.spin_duplicate_x.setValue(0.000000000000000)
        self.spin_duplicate_x.setDecimals(2)
        self.spin_duplicate_x.setSingleStep(1.000000000000000)

        self.gridLayout.addWidget(self.spin_duplicate_x, 0, 1, 1, 1)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)

        self.spin_duplicate_y = QDoubleSpinBox(self.widget)
        self.spin_duplicate_y.setObjectName(u"spin_duplicate_y")
        self.spin_duplicate_y.setMinimum(-1000.000000000000000)
        self.spin_duplicate_y.setMaximum(1000.000000000000000)
        self.spin_duplicate_y.setValue(0.000000000000000)
        self.spin_duplicate_y.setDecimals(2)
        self.spin_duplicate_y.setSingleStep(1.000000000000000)

        self.gridLayout.addWidget(self.spin_duplicate_y, 0, 3, 1, 1)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 4, 1, 1)

        self.spin_duplicate_z = QDoubleSpinBox(self.widget)
        self.spin_duplicate_z.setObjectName(u"spin_duplicate_z")
        self.spin_duplicate_z.setMinimum(-1000.000000000000000)
        self.spin_duplicate_z.setMaximum(1000.000000000000000)
        self.spin_duplicate_z.setValue(0.000000000000000)
        self.spin_duplicate_z.setDecimals(2)
        self.spin_duplicate_z.setSingleStep(1.000000000000000)

        self.gridLayout.addWidget(self.spin_duplicate_z, 0, 5, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)


        self.verticalLayout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox(dialog_duplicate)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dialog_duplicate)
        self.buttonBox.accepted.connect(dialog_duplicate.accept)
        self.buttonBox.rejected.connect(dialog_duplicate.reject)

        QMetaObject.connectSlotsByName(dialog_duplicate)
    # setupUi

    def retranslateUi(self, dialog_duplicate):
        dialog_duplicate.setWindowTitle(QCoreApplication.translate("DialogDuplicate", u"Duplicate Plate", None))
        self.duplicate_label.setText(QCoreApplication.translate("DialogDuplicate", u"Creating a duplicate:", None))
        self.radio_btn_relative_coords.setText(QCoreApplication.translate("DialogDuplicate", u"Use relative coordinates to original position", None))
        self.radio_btn_absolute_pos.setText(QCoreApplication.translate("DialogDuplicate", u"Use absolute positions, center", None))
        self.label.setText(QCoreApplication.translate("DialogDuplicate", u"x:", None))
        self.label_2.setText(QCoreApplication.translate("DialogDuplicate", u"y:", None))
        self.label_3.setText(QCoreApplication.translate("DialogDuplicate", u"z:", None))
    # retranslateUi

