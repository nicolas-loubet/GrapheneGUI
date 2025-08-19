from PySide6.QtWidgets import QDialog
from ..ui.dialog_create_ui import Ui_DialogCreate
from ..ui.dialog_duplicate_ui import Ui_DialogDuplicate
from ..ui.dialog_prob_ui import Ui_DialogProb
from ..ui.dialog_cnt_ui import Ui_CNTDialog

class CreateDialog(QDialog, Ui_DialogCreate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

class DuplicateDialog(QDialog, Ui_DialogDuplicate):
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

class CNTDialog(QDialog, Ui_CNTDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.spin_vec_x.setEnabled(False)
        self.spin_vec_y.setEnabled(False)
        self.combo_type.currentIndexChanged.connect(self.on_type_changed)

    def on_type_changed(self, index):
        self.spin_vec_x.setEnabled(index == 2)
        self.spin_vec_y.setEnabled(index == 2)

    def get_vector(self, bounds):
        if self.combo_type.currentIndex() == 0:
            return [bounds[0],0]
        elif self.combo_type.currentIndex() == 1:
            return [0,bounds[1]+.142]
        else:
            return [self.spin_vec_x.value(), self.spin_vec_y.value()]