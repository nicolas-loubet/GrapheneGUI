from PySide6.QtWidgets import QDialog
from ..ui.dialog_create_ui import Ui_DialogCreate
from ..ui.dialog_duplicate_ui import Ui_DialogDuplicate
from ..ui.dialog_prob_ui import Ui_DialogProb
from ..ui.dialog_cnt_ui import Ui_CNTDialog
from ..ui.atom_type_ui import Ui_AtomTypeDialog
import numpy as np

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
        
class AtomTypeDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui= Ui_AtomTypeDialog()
        self.ui.setupUi(self)
        self.parent= parent

        self.ui.cb_water.currentIndexChanged.connect(self.update_water_params)
        self.ui.sb_epsilon_cc.valueChanged.connect(self.update_calculated)
        self.ui.sb_sigma_cc.valueChanged.connect(self.update_calculated)
        self.ui.sb_percent_epsilon.valueChanged.connect(self.adjust_epsilon_cc)
        self.ui.sb_percent_sigma.valueChanged.connect(self.adjust_sigma_cc)

    def update_water_params(self):
        model= self.ui.cb_water.currentText()
        epsilon_oo= self.parent.water_params[model]["epsilon"]
        sigma_oo= self.parent.water_params[model]["sigma"]
        self.ui.lbl_epsilon_oo.setText(f"{epsilon_oo:.6f}")
        self.ui.lbl_sigma_oo.setText(f"{sigma_oo:.6f}")
        self.parent.water_model= model
        self.update_calculated()

    def update_calculated(self):
        epsilon_cc= self.ui.sb_epsilon_cc.value()
        sigma_cc= self.ui.sb_sigma_cc.value()
        epsilon_oo= float(self.ui.lbl_epsilon_oo.text())
        sigma_oo= float(self.ui.lbl_sigma_oo.text())

        epsilon_co= np.sqrt(epsilon_cc * epsilon_oo)
        sigma_co= 0.5 * (sigma_cc + sigma_oo)

        self.ui.lbl_epsilon_co.setText(f"{epsilon_co:.6f}")
        self.ui.lbl_sigma_co.setText(f"{sigma_co:.6f}")

    def adjust_epsilon_cc(self):
        epsilon_cc= 0.359824
        percent= self.ui.sb_percent_epsilon.value() / 100
        epsilon_oo= float(self.ui.lbl_epsilon_oo.text())
        base_epsilon_co= np.sqrt(epsilon_cc * epsilon_oo)
        desired_epsilon_co= base_epsilon_co * percent
        new_epsilon_cc= (desired_epsilon_co ** 2) / epsilon_oo
        self.ui.sb_epsilon_cc.setValue(new_epsilon_cc)
        self.update_calculated()

    def adjust_sigma_cc(self):
        sigma_cc= 3.39967
        percent= self.ui.sb_percent_sigma.value() / 100
        sigma_oo= float(self.ui.lbl_sigma_oo.text())
        base_sigma_co= 0.5 * (sigma_cc + sigma_oo)
        desired_sigma_co= base_sigma_co * percent
        new_sigma_cc= 2 * desired_sigma_co - sigma_oo
        self.ui.sb_sigma_cc.setValue(new_sigma_cc)
        self.update_calculated()

    def get_data(self):
        return {
            "name": self.ui.le_name.text(),
            "epsilon": self.ui.sb_epsilon_cc.value(),
            "sigma": self.ui.sb_sigma_cc.value()
        }
