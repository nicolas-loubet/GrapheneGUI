from PySide6.QtWidgets import QDialog
from ui.dialog_create_ui import Ui_DialogCreate
from ui.dialog_duplicate_ui import Ui_DialogDuplicate
from ui.dialog_export_ui import Ui_DialogExport
from ui.dialog_import_ui import Ui_DialogImport
from ui.dialog_prob_ui import Ui_DialogProb

class CreateDialog(QDialog, Ui_DialogCreate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

class DuplicateDialog(QDialog, Ui_DialogDuplicate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

class ExportDialog(QDialog, Ui_DialogExport):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

class ImportDialog(QDialog, Ui_DialogImport):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

class ProbDialog(QDialog, Ui_DialogProb):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        self.spin_prob_oh.valueChanged.connect(self.on_oh_changed)
        self.spin_prob_o.valueChanged.connect(self.on_o_changed)
    
    def on_oh_changed(self, value):
        self.spin_prob_o.setValue(100 - value)
    
    def on_o_changed(self, value):
        self.spin_prob_oh.setValue(100 - value)
