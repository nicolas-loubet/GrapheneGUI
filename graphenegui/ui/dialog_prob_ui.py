# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_prob.ui'
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
    QGridLayout, QLabel, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_DialogProb(object):
    def setupUi(self, dialog_prob):
        if not dialog_prob.objectName():
            dialog_prob.setObjectName(u"dialog_prob")
        dialog_prob.setModal(True)
        self.verticalLayout = QVBoxLayout(dialog_prob)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(dialog_prob)
        self.widget.setObjectName(u"widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.spin_prob_oh = QSpinBox(self.widget)
        self.spin_prob_oh.setObjectName(u"spin_prob_oh")
        self.spin_prob_oh.setMinimum(0)
        self.spin_prob_oh.setMaximum(100)
        self.spin_prob_oh.setValue(66)
        self.spin_prob_oh.setSingleStep(1)

        self.gridLayout.addWidget(self.spin_prob_oh, 0, 1, 1, 1)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.spin_prob_o = QSpinBox(self.widget)
        self.spin_prob_o.setObjectName(u"spin_prob_o")
        self.spin_prob_o.setMinimum(0)
        self.spin_prob_o.setMaximum(100)
        self.spin_prob_o.setValue(34)
        self.spin_prob_o.setSingleStep(5)

        self.gridLayout.addWidget(self.spin_prob_o, 1, 1, 1, 1)


        self.verticalLayout.addWidget(self.widget)

        self.buttonBox = QDialogButtonBox(dialog_prob)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dialog_prob)
        self.buttonBox.accepted.connect(dialog_prob.accept)
        self.buttonBox.rejected.connect(dialog_prob.reject)

        QMetaObject.connectSlotsByName(dialog_prob)
    # setupUi

    def retranslateUi(self, dialog_prob):
        dialog_prob.setWindowTitle(QCoreApplication.translate("DialogProb", u"Oxidation Probabilities", None))
        self.label.setText(QCoreApplication.translate("DialogProb", u"OH Probability (%):", None))
        self.label_2.setText(QCoreApplication.translate("DialogProb", u"O Probability (%):", None))
    # retranslateUi

