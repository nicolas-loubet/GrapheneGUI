import os
import random
from .other_dialogs import CreateDialog, DuplicateDialog, ProbDialog, CNTDialog, AtomTypeDialog
from .renderer import Renderer
from .functionalities import *
from PySide6.QtWidgets import QMainWindow, QMessageBox, QGraphicsScene, QDialog, QFileDialog
from PySide6.QtCore import Slot, QEvent
from PySide6.QtGui import QPixmap
from ..ui.main_ui import Ui_MainWindow
from .export_formats import checkBounds

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        
        self.is_dark_mode = True
        self.active_oxide_mode = None
        self.first_carbon = None
        self.z_mode = 2  # 0: z+, 1: z-, 2: z±
        self.last_prob_oh = 66
        self.last_prob_o = 34
        self.plates = []
        self.plates_corresponding_to_duplicates = [[], []]  # [duplicates, bases]
        self.information_selected_atoms = []
        
        is_dark_mode_func = lambda: self.is_dark_mode

        self.renderer = Renderer(
            drawing_area=self.ui.graphicsView,
            ruler_x=self.ui.topRuler,
            ruler_y=self.ui.leftRuler,
            plates=self.plates,
            cb_plates=self.ui.comboDrawings,
            is_dark_mode_func=is_dark_mode_func
        )

        self.buttons_that_depend_of_having_a_plate(False)
        self.ui.radioZpm.setChecked(True)

        self.atom_types = {
            "ca": {"epsilon": 0.359824, "sigma": 3.39967}
        }
        self.water_model = "TIP3P"
        self.water_params = {
            "TIP3P": {"epsilon": 0.6364, "sigma": 3.15061},
            "TIP4P": {"epsilon": 0.6480, "sigma": 3.15365},
            "TIP4P/2005": {"epsilon": 0.7749, "sigma": 3.1589},
            "TIP5P": {"epsilon": 0.6694, "sigma": 3.12},
            "TIP5P-2018": {"epsilon": 0.79, "sigma": 3.145},
            "SPC": {"epsilon": 0.650, "sigma": 3.166},
            "SPC/E": {"epsilon": 0.650, "sigma": 3.166},
        }

        self.ui.comboCType.clear()
        for typ in self.atom_types.keys():
            self.ui.comboCType.addItem(typ)

        self.setup_connections()
        load_css(self)

    def setup_connections(self):
        self.ui.btnCreate.clicked.connect(self.handle_btn_create_clicked)
        self.ui.comboDrawings.currentIndexChanged.connect(self.handle_cb_plates_changed)
        self.ui.btnDuplicate.clicked.connect(self.handle_btn_duplicate_clicked)
        self.ui.btnDelete.clicked.connect(self.handle_btn_delete_clicked)
        self.ui.btnImport.clicked.connect(self.handle_btn_import_clicked)
        self.ui.btnExport.clicked.connect(self.handle_btn_export_clicked)
        self.ui.btnCNT.clicked.connect(self.handle_btn_cnt_clicked)
        self.ui.btnTheme.clicked.connect(self.handle_btn_dark_light_mode_clicked)
        self.ui.btnReduceAll.clicked.connect(self.handle_btn_reduce_clicked)
        self.ui.btnChangeProb.clicked.connect(self.handle_btn_change_prob_clicked)
        self.ui.spinRandom.valueChanged.connect(self.handle_spin_random_value_changed)
        self.ui.entryVMD.textChanged.connect(self.handle_entry_selection_changed)
        self.ui.btnAddOH.clicked.connect(self.handle_btn_oh_clicked)
        self.ui.btnAddO.clicked.connect(self.handle_btn_o_clicked)
        self.ui.btnRemoveOx.clicked.connect(self.handle_btn_remove_ox_clicked)
        self.ui.btnAddOxidation.clicked.connect(self.handle_btn_add_oxidation_clicked)
        self.ui.comboCType.currentIndexChanged.connect(self.handle_ctype_changed)
        self.ui.btnAddCType.clicked.connect(self.handle_btn_add_ctype_clicked)
        
        self.ui.radioZp.toggled.connect(lambda: self.handle_radio_toggled(self.ui.radioZp))
        self.ui.radioZm.toggled.connect(lambda: self.handle_radio_toggled(self.ui.radioZm))
        self.ui.radioZpm.toggled.connect(lambda: self.handle_radio_toggled(self.ui.radioZpm))
        
        self.ui.graphicsView.viewport().installEventFilter(self)

        self.scene.mousePressEvent = self.handle_drawing_area_clicked


    # ================================
    # Overrides
    # ================================
    def showEvent(self, event):
        super().showEvent(event)
        self.update_drawing_area()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_drawing_area()

    def closeEvent(self, event):
        print("\nThanks for using Graphene-GUI")
        print("Please cite: No cite yet, stay in touch!")
    

    # ================================
    # State functions
    # ================================
    def buttons_that_depend_of_having_a_plate(self, active):
        self.ui.btnDuplicate.setEnabled(active)
        self.ui.btnDelete.setEnabled(active)
        self.ui.btnExport.setEnabled(active)
        self.ui.btnCNT.setEnabled(active)
        self.ui.btnReduceAll.setEnabled(active)
        self.ui.btnChangeProb.setEnabled(active)
        self.ui.spinRandom.setEnabled(active)
        self.ui.entryVMD.setEnabled(active)
        self.ui.btnAddOH.setEnabled(active)
        self.ui.btnAddO.setEnabled(active)
        self.ui.btnRemoveOx.setEnabled(active)
        self.ui.radioZpm.setEnabled(active)
        self.ui.radioZp.setEnabled(active)
        self.ui.radioZm.setEnabled(active)
        self.ui.btnAddOxidation.setEnabled(active)

    def eventFilter(self, source, event):
        if(source is self.ui.graphicsView.viewport() and event.type() == QEvent.Resize):
            self.update_drawing_area()
        return super().eventFilter(source, event)


    # ================================
    # Top panel
    # ================================
    @Slot()
    def handle_btn_create_clicked(self):
        dialog = CreateDialog(self)
        if dialog.exec() != QDialog.Accepted: return

        try:
            create_plate(dialog, self)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    @Slot(int)
    def handle_cb_plates_changed(self, index):
        self.update_drawing_area()

    @Slot()
    def handle_btn_duplicate_clicked(self):
        dialog = DuplicateDialog(self)
        if dialog.exec() != QDialog.Accepted: return

        try:
            create_duplicate(self, dialog)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def handle_btn_delete_clicked(self):
        delete_actual_plate(self)
        self.renderer.update_view()

    @Slot()
    def handle_btn_import_clicked(self):
        filters = "All Files (*);;GRO Files (*.gro);;XYZ Files (*.xyz);;PDB Files (*.pdb);;MOL2 Files (*.mol2)"
        file_name, _ = QFileDialog.getOpenFileName(self, "Import File", "", filters)

        if not file_name: return

        ext = os.path.splitext(file_name)[1].lower()
        try:
            import_file(ext, file_name, self)
        except Exception as e:
            QMessageBox.critical(self, "Error reading file", str(e))

    @Slot()
    def handle_btn_export_clicked(self):
        export_file(self)
    
    @Slot()
    def handle_btn_cnt_clicked(self):
        plate = self.plates[self.ui.comboDrawings.currentIndex()]
        if plate.get_is_CNT():
            plate.restore_plate()
            self.buttons_that_depend_of_having_a_plate(True)
        else:
            atoms = plate.get_carbon_coords() + plate.get_oxide_coords()

            _, bounds = checkBounds([plate])

            dialog= CNTDialog(self)
            if dialog.exec() != QDialog.Accepted: return

            roll_vec= dialog.get_vector(bounds)
            if roll_vec is None or (roll_vec[0] == 0 and roll_vec[1] == 0):
                QMessageBox.warning(self, "Invalid vector", "Please select a valid CNT option or enter a valid custom vector.")
                return

            self.renderer.set_roll_vector(roll_vec)
            new_atoms = roll_atoms_as_CNT(atoms, roll_vec, plate.get_geometric_center())
            plate.set_is_CNT(True)
            plate.set_atoms(new_atoms)
            self.buttons_that_depend_of_having_a_plate(False)
            self.ui.btnExport.setEnabled(True)
            self.ui.btnDelete.setEnabled(True)
            self.ui.btnCNT.setEnabled(True)
        self.update_drawing_area()
        
    @Slot()
    def handle_btn_dark_light_mode_clicked(self):
        self.is_dark_mode = not self.is_dark_mode
        load_css(self)
        self.update_drawing_area()
        print(f"Switched to {'dark' if self.is_dark_mode else 'light'} mode")


    # ================================
    # Drawing area, central panel
    # ================================
    def clicked_carbon_add_OH(self, plate, carbon, z_sign, i_atom):
        cx, cy, cz = carbon[:3]
        o_x = cx
        o_y = cy
        o_z = cz + z_sign * 0.149
        h_x = cx + .093
        h_z = o_z + z_sign * 0.032

        if not plate.is_position_occupied(o_x, o_y, o_z):
            plate.add_oxide(o_x, o_y, o_z, "OO", i_atom)
            i_atom += 1
            plate.add_oxide(h_x, o_y, h_z, "HO", i_atom)
            self.update_drawing_area()
            print(f"Added O at ({o_x*10:.2f}, {o_y*10:.2f}, {o_z*10:.2f}) and H at ({h_x:.3f}, {o_y:.3f}, {h_z:.3f})")
            print(f"Actual oxidation rate: {(plate.get_oxide_count()/len(plate.get_carbon_coords()))*100:.2f}%")
        else:
            print("Position already occupied by an oxide")

    def clicked_carbon_add_O(self, plate, carbon, z_sign, i_atom):
        adjacent_carbons = plate.carbons_adjacent(self.first_carbon)
        if carbon in adjacent_carbons:
            c1_x, c1_y, c1_z = self.first_carbon[:3]
            c2_x, c2_y = carbon[:2]
            o_x = (c1_x + c2_x) / 2
            o_y = (c1_y + c2_y) / 2
            o_z = c1_z + z_sign * 0.126

            if not plate.is_position_occupied(o_x, o_y, o_z):
                plate.add_oxide(o_x, o_y, o_z, "OE", i_atom)
                self.update_drawing_area()
                print(f"Added O at ({o_x*10:.2f}, {o_y*10:.2f}, {o_z*10:.2f})")
                print(f"Actual oxidation rate: {(plate.get_oxide_count()/len(plate.get_carbon_coords()))*100:.2f}%")
            else:
                print("Position already occupied by an oxide")
        else:
            print("Second carbon is not adjacent to the first")
        self.first_carbon = None

    def handle_drawing_area_clicked(self, event):
        if self.ui.comboDrawings.currentIndex() == -1 or not self.active_oxide_mode: return

        manage_duplicates_for_deletion(self, self.ui.comboDrawings.currentIndex()+1, False)

        plate = self.plates[self.ui.comboDrawings.currentIndex()]
        pos = event.scenePos()
        x_nm, y_nm = self.renderer.pixel_to_nm(pos.x(), pos.y())
        carbon = plate.get_nearest_carbon(x_nm, y_nm)
        if not carbon: return

        i_atom = plate.get_number_atoms() + 1
        z_sign = 1 if self.z_mode == 0 else -1 if self.z_mode == 1 else random.choice([-1, 1])

        if self.active_oxide_mode == "OH":
            self.clicked_carbon_add_OH(plate, carbon, z_sign, i_atom)
        elif self.active_oxide_mode == "O":
            if self.first_carbon is None:
                self.first_carbon = carbon
                print("First carbon selected, click an adjacent carbon")
            else:
                self.clicked_carbon_add_O(plate, carbon, z_sign, i_atom)
        elif self.active_oxide_mode == "Remove":
            list_remove_ox = plate.get_oxides_for_carbon(carbon)
            for ox in list_remove_ox:
                plate.remove_atom_oxide(ox)
            self.update_drawing_area()
            plate.recheck_ox_indexes()
            print(f"{len(list_remove_ox)} atom{'s' if len(list_remove_ox) != 1 else ''} removed")

    def update_drawing_area(self):
        active_index = self.ui.comboDrawings.currentIndex()
        
        if active_index != -1 and self.plates and self.plates[active_index].get_number_atoms():
            img = self.renderer.render_plate(self.plates[active_index], self.is_dark_mode)
            self.renderer.update_view()
            pixmap = QPixmap.fromImage(img)
            self.scene.addPixmap(pixmap)

        self.ui.comboDrawings.setEnabled(active_index != -1)


    # ================================
    # Lower panel
    # ================================
    @Slot()
    def handle_btn_reduce_clicked(self):
        if self.ui.comboDrawings.currentIndex() == -1: return
        manage_duplicates_for_deletion(self, self.ui.comboDrawings.currentIndex()+1, False)

        plate = self.plates[self.ui.comboDrawings.currentIndex()]
        plate.remove_oxides()
        self.update_drawing_area()
        self.ui.spinRandom.setValue(0)
        self.ui.entryVMD.setText("")
        print("Oxides removed")

    @Slot()
    def handle_btn_change_prob_clicked(self):
        dialog = ProbDialog(self)
        dialog.spin_prob_oh.setValue(self.last_prob_oh)
        dialog.spin_prob_o.setValue(self.last_prob_o)
        if dialog.exec() == QDialog.Accepted:
            self.last_prob_oh = dialog.spin_prob_oh.value()
            self.last_prob_o = dialog.spin_prob_o.value()

    def expr_changed(self):
        if self.ui.comboDrawings.currentIndex() == -1: return
        information_selected_atoms= select_atoms_expr(self, self.ui.entryVMD.text())
        self.information_selected_atoms= information_selected_atoms
        if not information_selected_atoms:
            self.renderer.highlighted_atoms= []
            self.update_drawing_area()
            return
        self.renderer.highlighted_atoms= information_selected_atoms
        self.update_drawing_area()

    @Slot()
    def handle_btn_add_ctype_clicked(self):
        dialog= AtomTypeDialog(self)
        dialog.ui.cb_water.setCurrentText(self.water_model)
        dialog.update_water_params()
        dialog.update_calculated()
        if dialog.exec() == QDialog.Accepted:
            data= dialog.get_data()
            name= data["name"]
            if len(name) > 4:
                QMessageBox.warning(self, "Error", "Type name cannot be longer than 4 characters.")
                return
            if name in self.atom_types:
                QMessageBox.warning(self, "Error", "Type name already exists.")
                return
            if "c"+name in self.atom_types:
                QMessageBox.warning(self, "Error", "Type name could be ambiguous because of charged C atoms, choose another name.")
                return
            if not name:
                QMessageBox.warning(self, "Error", "Type name cannot be empty.")
                return
            self.atom_types[name]= {"epsilon": data["epsilon"], "sigma": data["sigma"]}
            self.ui.comboCType.addItem(name)
            self.ui.comboCType.setCurrentText(name)
            print(f"Added new carbon type '{name}' with epsilon={data['epsilon']}, sigma={data['sigma']}")

    @Slot(int)
    def handle_ctype_changed(self, index):
        if index < 0: return
        new_type= self.ui.comboCType.currentText()
        if self.renderer.highlighted_atoms:
            plate= self.plates[self.ui.comboDrawings.currentIndex()]
            for carbon in self.renderer.highlighted_atoms:
                plate.set_carbon_type(carbon, new_type)
            print(f"Changed {len(self.renderer.highlighted_atoms)} carbons to type '{new_type}'")
            self.renderer.highlighted_atoms= []  
        self.update_drawing_area()


    @Slot(int)
    def handle_spin_random_value_changed(self, value):
        self.expr_changed()

    @Slot(str)
    def handle_entry_selection_changed(self, text):
        self.expr_changed()

    @Slot()
    def handle_btn_add_oxidation_clicked(self):
        if self.ui.comboDrawings.currentIndex() == -1: return
        if not self.information_selected_atoms: return
        put_oxides(self, self.information_selected_atoms)
        self.renderer.highlighted_atoms= []
        self.information_selected_atoms= []




    # ================================
    # Lateral panel
    # ================================
    def set_oxide_mode(self, mode):
        self.active_oxide_mode= mode
        self.first_carbon= None

        self.ui.btnAddOH.setChecked(mode == "OH")
        self.ui.btnAddO.setChecked(mode == "O")
        self.ui.btnRemoveOx.setChecked(mode == "Remove")

    def handle_btn_oh_clicked(self):
        if self.ui.comboDrawings.currentIndex() == -1: return
        plate= self.plates[self.ui.comboDrawings.currentIndex()]
        carbons= self.renderer.highlighted_atoms
        if carbons:
            count= plate.add_oxydation_to_list_of_carbon(carbons, self.z_mode, 100)
            self.renderer.highlighted_atoms = []
            self.update_drawing_area()
            print(f"Forced OH oxidation applied ({count} carbons modified), that is {plate.get_oxide_count()/plate.get_number_atoms()*100:.2f}% of the selected part of the plate")
            self.set_oxide_mode(None)
        else:
            if self.ui.btnAddOH.isChecked():
                if self.active_oxide_mode:
                    print(f"{self.active_oxide_mode} mode deactivated")
                self.ui.btnAddO.setChecked(False)
                self.ui.btnRemoveOx.setChecked(False)
                self.set_oxide_mode("OH")
                print("OH mode activated")
            else:
                self.set_oxide_mode(None)
                print("OH mode deactivated")

    @Slot()
    def handle_btn_o_clicked(self):
        if self.ui.comboDrawings.currentIndex() == -1: return
        plate= self.plates[self.ui.comboDrawings.currentIndex()]
        carbons= self.renderer.highlighted_atoms if self.renderer.highlighted_atoms else []
        if carbons:
            count= plate.add_oxydation_to_list_of_carbon(carbons, self.z_mode, 0)
            self.renderer.highlighted_atoms= []
            self.update_drawing_area()
            print(f"Forced O (epoxy) oxidation applied ({count} carbons modified), that is {plate.get_oxide_count()/plate.get_number_atoms()*100:.2f}% of the selected part of the plate")
            self.set_oxide_mode(None)
        else:
            if self.ui.btnAddO.isChecked():
                if self.active_oxide_mode:
                    print(f"{self.active_oxide_mode} mode deactivated")
                self.ui.btnAddOH.setChecked(False)
                self.ui.btnRemoveOx.setChecked(False)
                self.set_oxide_mode("O")
                print("O (epoxy) mode activated")
            else:
                self.set_oxide_mode(None)
                print("O (epoxy) mode deactivated")

    @Slot()
    def handle_btn_remove_ox_clicked(self):
        if self.ui.btnRemoveOx.isChecked():
            if self.active_oxide_mode:
                print(f"{self.active_oxide_mode} mode deactivated")
            self.ui.btnAddOH.setChecked(False)
            self.ui.btnAddO.setChecked(False)
            self.set_oxide_mode("Remove")
            print("Remove mode activated")
        else:
            self.set_oxide_mode(None)
            print("Remove mode deactivated")

    def handle_radio_toggled(self, radio_button):
        if radio_button == self.ui.radioZp and radio_button.isChecked():
            self.z_mode = 0
        elif radio_button == self.ui.radioZm and radio_button.isChecked():
            self.z_mode = 1
        elif radio_button == self.ui.radioZpm and radio_button.isChecked():
            self.z_mode = 2
