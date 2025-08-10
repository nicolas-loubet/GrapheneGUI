# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_export.ui'
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

class Ui_DialogExport(object):
    def setupUi(self, dialog_export):
        if not dialog_export.objectName():
            dialog_export.setObjectName(u"dialog_export")
        dialog_export.setModal(True)
        self.verticalLayout = QVBoxLayout(dialog_export)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.fileChooserWidget = QWidget(dialog_export)
        self.fileChooserWidget.setObjectName(u"fileChooserWidget")
        self.verticalLayout_2 = QVBoxLayout(self.fileChooserWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.fileDialog = QFileDialog(self.fileChooserWidget)
        self.fileDialog.setObjectName(u"fileDialog")
        self.fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        self.fileDialog.setFileMode(QFileDialog.AnyFile)
        self.fileDialog.setOptions(QFileDialog.DontConfirmOverwrite|QFileDialog.DontUseNativeDialog)

        self.verticalLayout_2.addWidget(self.fileDialog)


        self.verticalLayout.addWidget(self.fileChooserWidget)

        self.buttonBox = QDialogButtonBox(dialog_export)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dialog_export)
        self.buttonBox.accepted.connect(dialog_export.accept)
        self.buttonBox.rejected.connect(dialog_export.reject)

        QMetaObject.connectSlotsByName(dialog_export)
    # setupUi

    def retranslateUi(self, dialog_export):
        dialog_export.setWindowTitle(QCoreApplication.translate("DialogExport", u"Export Graphene File", None))
    # retranslateUi

