# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_import.ui'
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
    QFileDialog, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogImport(object):
    def setupUi(self, dialog_import):
        if not dialog_import.objectName():
            dialog_import.setObjectName(u"dialog_import")
        dialog_import.setModal(True)
        self.verticalLayout = QVBoxLayout(dialog_import)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.fileChooserWidget = QWidget(dialog_import)
        self.fileChooserWidget.setObjectName(u"fileChooserWidget")
        self.verticalLayout_2 = QVBoxLayout(self.fileChooserWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.fileDialog = QFileDialog(self.fileChooserWidget)
        self.fileDialog.setObjectName(u"fileDialog")
        self.fileDialog.setAcceptMode(QFileDialog.AcceptOpen)
        self.fileDialog.setFileMode(QFileDialog.ExistingFile)
        self.fileDialog.setOptions(QFileDialog.DontUseNativeDialog)

        self.verticalLayout_2.addWidget(self.fileDialog)


        self.verticalLayout.addWidget(self.fileChooserWidget)

        self.buttonBox = QDialogButtonBox(dialog_import)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Open)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dialog_import)
        self.buttonBox.accepted.connect(dialog_import.accept)
        self.buttonBox.rejected.connect(dialog_import.reject)

        QMetaObject.connectSlotsByName(dialog_import)
    # setupUi

    def retranslateUi(self, dialog_import):
        dialog_import.setWindowTitle(QCoreApplication.translate("DialogImport", u"Import Graphene File", None))
    # retranslateUi

