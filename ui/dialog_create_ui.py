# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_create.ui'
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
    QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogCreate(object):
    def setupUi(self, dialog_create):
        if not dialog_create.objectName():
            dialog_create.setObjectName(u"dialog_create")
        dialog_create.setModal(True)
        self.verticalLayout = QVBoxLayout(dialog_create)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(dialog_create)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.spin_width = QDoubleSpinBox(self.widget)
        self.spin_width.setObjectName(u"spin_width")
        self.spin_width.setMinimum(1.000000000000000)
        self.spin_width.setMaximum(1000.000000000000000)
        self.spin_width.setValue(50.000000000000000)
        self.spin_width.setDecimals(2)
        self.spin_width.setSingleStep(0.100000000000000)

        self.gridLayout.addWidget(self.spin_width, 0, 1, 1, 1)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.spin_height = QDoubleSpinBox(self.widget)
        self.spin_height.setObjectName(u"spin_height")
        self.spin_height.setMinimum(1.000000000000000)
        self.spin_height.setMaximum(1000.000000000000000)
        self.spin_height.setValue(50.000000000000000)
        self.spin_height.setDecimals(2)
        self.spin_height.setSingleStep(0.100000000000000)

        self.gridLayout.addWidget(self.spin_height, 1, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_3.addWidget(self.label_3)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 1)

        self.spin_center_x = QDoubleSpinBox(self.widget)
        self.spin_center_x.setObjectName(u"spin_center_x")
        self.spin_center_x.setMinimum(0.000000000000000)
        self.spin_center_x.setMaximum(1000.000000000000000)
        self.spin_center_x.setValue(0.000000000000000)
        self.spin_center_x.setDecimals(2)
        self.spin_center_x.setSingleStep(1.000000000000000)

        self.gridLayout_2.addWidget(self.spin_center_x, 0, 1, 1, 1)

        self.label_5 = QLabel(self.widget)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_2.addWidget(self.label_5, 0, 2, 1, 1)

        self.spin_center_y = QDoubleSpinBox(self.widget)
        self.spin_center_y.setObjectName(u"spin_center_y")
        self.spin_center_y.setMinimum(0.000000000000000)
        self.spin_center_y.setMaximum(1000.000000000000000)
        self.spin_center_y.setValue(0.000000000000000)
        self.spin_center_y.setDecimals(2)
        self.spin_center_y.setSingleStep(1.000000000000000)

        self.gridLayout_2.addWidget(self.spin_center_y, 0, 3, 1, 1)

        self.label_6 = QLabel(self.widget)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 0, 4, 1, 1)

        self.spin_center_z = QDoubleSpinBox(self.widget)
        self.spin_center_z.setObjectName(u"spin_center_z")
        self.spin_center_z.setMinimum(0.000000000000000)
        self.spin_center_z.setMaximum(1000.000000000000000)
        self.spin_center_z.setValue(0.000000000000000)
        self.spin_center_z.setDecimals(2)
        self.spin_center_z.setSingleStep(1.000000000000000)

        self.gridLayout_2.addWidget(self.spin_center_z, 0, 5, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_7 = QLabel(self.widget)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout.addWidget(self.label_7)

        self.spin_scale = QDoubleSpinBox(self.widget)
        self.spin_scale.setObjectName(u"spin_scale")
        self.spin_scale.setMinimum(1.000000000000000)
        self.spin_scale.setMaximum(1000.000000000000000)
        self.spin_scale.setValue(100.000000000000000)
        self.spin_scale.setDecimals(2)
        self.spin_scale.setSingleStep(10.000000000000000)

        self.horizontalLayout.addWidget(self.spin_scale)

        self.label_8 = QLabel(self.widget)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout.addWidget(self.label_8)


        self.verticalLayout_3.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox(dialog_create)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dialog_create)
        self.buttonBox.accepted.connect(dialog_create.accept)
        self.buttonBox.rejected.connect(dialog_create.reject)

        QMetaObject.connectSlotsByName(dialog_create)
    # setupUi

    def retranslateUi(self, dialog_create):
        dialog_create.setWindowTitle(QCoreApplication.translate("DialogCreate", u"Create Graphene", None))
        self.label.setText(QCoreApplication.translate("DialogCreate", u"Width (\u00c5):", None))
        self.label_2.setText(QCoreApplication.translate("DialogCreate", u"Height (\u00c5):", None))
        self.label_3.setText(QCoreApplication.translate("DialogCreate", u"Center at:", None))
        self.label_4.setText(QCoreApplication.translate("DialogCreate", u"x:", None))
        self.label_5.setText(QCoreApplication.translate("DialogCreate", u"y:", None))
        self.label_6.setText(QCoreApplication.translate("DialogCreate", u"z:", None))
        self.label_7.setText(QCoreApplication.translate("DialogCreate", u"Scale factor:", None))
        self.label_8.setText(QCoreApplication.translate("DialogCreate", u"%", None))
    # retranslateUi

