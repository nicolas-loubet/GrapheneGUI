import os
import random
import threading
import math
from logic.other_dialogs import CreateDialog, DuplicateDialog, ProbDialog
from logic.graphene import Graphene, generatePatterns
from logic.renderer import Renderer
from logic.export_formats import writeGRO, writeXYZ, writeTOP, writePDB, writeMOL2
from logic.import_formats import readGRO, readXYZ, readPDB, readMOL2
from PySide6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox,
    QGraphicsScene, QDialog, QButtonGroup)
from PySide6.QtCore import Qt, Slot, QEvent
from PySide6.QtGui import QPixmap
from ui.main_ui import Ui_MainWindow

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
        
        is_dark_mode_func = lambda: self.is_dark_mode

        self.ui.topRuler.setStyleSheet("background-color: #3d3d3d;")
        self.ui.leftRuler.setStyleSheet("background-color: #3d3d3d;")
        
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

        self.setup_connections()

    def setup_connections(self):
        self.ui.btnCreate.clicked.connect(self.handle_btn_create_clicked)
        self.ui.comboDrawings.currentIndexChanged.connect(self.handle_cb_plates_changed)
        self.ui.btnDuplicate.clicked.connect(self.handle_btn_duplicate_clicked)
        self.ui.btnDelete.clicked.connect(self.handle_btn_delete_clicked)
        self.ui.btnImport.clicked.connect(self.handle_btn_import_clicked)
        self.ui.btnExport.clicked.connect(self.handle_btn_export_clicked)
        self.ui.btnTheme.clicked.connect(self.handle_btn_dark_light_mode_clicked)
        self.ui.btnReduceAll.clicked.connect(self.handle_btn_reduce_clicked)
        self.ui.btnChangeProb.clicked.connect(self.handle_btn_change_prob_clicked)
        self.ui.spinRandom.valueChanged.connect(self.handle_spin_random_value_changed)
        self.ui.entryVMD.textChanged.connect(self.handle_entry_selection_changed)
        self.ui.btnAddOH.clicked.connect(self.handle_btn_oh_clicked)
        self.ui.btnAddO.clicked.connect(self.handle_btn_o_clicked)
        self.ui.btnRemoveOx.clicked.connect(self.handle_btn_remove_ox_clicked)
        
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
            width = dialog.spin_width.value()
            height = dialog.spin_height.value()
            center_x = dialog.spin_center_x.value()
            center_y = dialog.spin_center_y.value()
            center_z = dialog.spin_center_z.value()
            factor = dialog.spin_scale.value()/100.0

            width_nm = width / 10
            height_nm = height / 10
            center_x_nm = center_x / 10
            center_y_nm = center_y / 10
            center_z_nm = center_z / 10

            n_x = math.floor(width_nm / (2 * 0.1225 * factor))
            n_y = math.floor(height_nm / (6 * 0.071 * factor))+1

            max_atoms = len(generatePatterns())
            max_n_x_n_y = max_atoms // (2 * (2 * n_x + 1)) if n_x > 0 else 0
            if n_y > max_n_x_n_y:
                QMessageBox.critical(
                    self, 
                    "Too large", 
                    f"The number of atoms is too large ({max_atoms}). Reduce the width or height."
                )
                return

            plate = Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor)
            self.plates.append(plate)

            self.ui.comboDrawings.addItem(f"Plate {len(self.plates)}")
            self.ui.comboDrawings.setCurrentIndex(len(self.plates) - 1)

            self.load_css()
            self.update_drawing_area()
            self.buttons_that_depend_of_having_a_plate(True)
            print(f"Coords drawn: Plate {len(self.plates)}")

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
            index_base = self.ui.comboDrawings.currentIndex()+1
        
            plate = self.plates[self.ui.comboDrawings.currentIndex()]
            translation = [
                dialog.spin_duplicate_x.value(),
                dialog.spin_duplicate_y.value(),
                dialog.spin_duplicate_z.value()
            ]
            for i in range(3): 
                translation[i] *= .1  # Change to nm
            
            if dialog.radio_btn_absolute_pos.isChecked():
                plate_actual_center = plate.get_geometric_center()
                for i in range(3):
                    translation[i] -= plate_actual_center[i]

            self.plates.append(plate.duplicate(translation))

            while(index_base in self.plates_corresponding_to_duplicates[0]):
                index_in_list = self.plates_corresponding_to_duplicates[0].index(index_base)
                index_base = self.plates_corresponding_to_duplicates[1][index_in_list]
            
            self.plates_corresponding_to_duplicates[0].append(len(self.plates))
            self.plates_corresponding_to_duplicates[1].append(index_base)

            self.ui.comboDrawings.addItem(f"Plate {len(self.plates)}")
            print(f"Duplicate added: Plate {len(self.plates)}")
            self.ui.comboDrawings.setCurrentIndex(len(self.plates)-1)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def handle_btn_delete_clicked(self):
        index = self.ui.comboDrawings.currentIndex()
        if index < 0: return

        self.manage_duplicates_for_deletion(index+1, True)

        self.plates.pop(index)
        self.ui.comboDrawings.clear()
        for i in range(len(self.plates)):
            self.ui.comboDrawings.addItem(f"Plate {i + 1}")
        
        if self.plates:
            self.ui.comboDrawings.setCurrentIndex(0)
        else:
            self.ui.comboDrawings.setCurrentIndex(-1)
            self.buttons_that_depend_of_having_a_plate(False)
            self.ui.spinRandom.setValue(0)
            self.ui.entryVMD.setText("")

        self.update_drawing_area()
        print(f"Plate {index+1} deleted")

    @Slot()
    def handle_btn_import_clicked(self):
        filters = "GRO Files (*.gro);;XYZ Files (*.xyz);;PDB Files (*.pdb);;MOL2 Files (*.mol2);;All Files (*)"
        file_name, _ = QFileDialog.getOpenFileName(self, "Import File", "", filters)

        if not file_name: return

        ext = os.path.splitext(file_name)[1].lower()
        try:
            if ext == ".gro":
                new_plates = readGRO(file_name)
            elif ext == ".xyz":
                new_plates = readXYZ(file_name)
            elif ext == ".pdb":
                new_plates = readPDB(file_name)
            elif ext == ".mol2":
                new_plates = readMOL2(file_name)
            else:
                raise ValueError(f"Not supported file extension: {ext}")

            for plate in new_plates:
                self.plates.append(plate)
                idx = len(self.plates)
                self.ui.comboDrawings.addItem(f"Plate {idx}")
                print(f"Importing coords: Plate {idx}")

            if new_plates:
                self.ui.comboDrawings.setCurrentIndex(len(self.plates) - 1)
                self.buttons_that_depend_of_having_a_plate(True)
                self.update_drawing_area()

            print(f"{len(new_plates)} plate(s) imported from {file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error reading file", str(e))


    @Slot()
    def handle_btn_export_clicked(self):
        filters = (
            "GRO Files (*.gro);;"
            "PDB Files (*.pdb);;"
            "XYZ Files (*.xyz);;"
            "MOL2 Files (*.mol2);;"
            "TOP Files (*.top);;"
            "All Files (*)"
        )
        file_name, selected_filter = QFileDialog.getSaveFileName(self, "Export File", "", filters)

        if not file_name: return

        ext_map = {
            "GRO": ".gro",
            "PDB": ".pdb",
            "XYZ": ".xyz",
            "MOL2": ".mol2",
            "TOP": ".top"
        }
        if '.' not in file_name:
            for key, ext in ext_map.items():
                if key in selected_filter:
                    file_name += ext
                    break

        if file_name.endswith(".gro"):
            writeGRO(file_name, self.plates)
        elif file_name.endswith(".pdb"):
            writePDB(file_name, self.plates)
        elif file_name.endswith(".xyz"):
            writeXYZ(file_name, self.plates)
        elif file_name.endswith(".mol2"):
            writeMOL2(file_name, self.plates)
        elif file_name.endswith(".top"):
            factor = self.spin_scale.value() / 100.0
            QMessageBox.information(self, "Exporting topology", "Exporting topology...")

            def export_top_and_close():
                writeTOP(file_name, self.plates, factor, self.plates_corresponding_to_duplicates)
                QMessageBox.information(self, "Export Complete", "Topology export completed")

            threading.Thread(target=export_top_and_close, daemon=True).start()

    @Slot()
    def handle_btn_dark_light_mode_clicked(self):
        self.is_dark_mode = not self.is_dark_mode
        self.load_css()
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
        if self.ui.comboDrawings.currentIndex() == -1 or not self.active_oxide_mode:
            return

        self.manage_duplicates_for_deletion(self.ui.comboDrawings.currentIndex()+1, False)

        plate = self.plates[self.ui.comboDrawings.currentIndex()]
        pos = event.scenePos()
        x, y = pos.x(), pos.y()

        # Convert pixels to nm
        x_nm, y_nm = self.renderer.pixel_to_nm(x, y)

        carbon = plate.get_nearest_carbon(x_nm, y_nm)
        if not carbon:
            return

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
        if self.ui.comboDrawings.currentIndex() == -1:
            return
        self.manage_duplicates_for_deletion(self.ui.comboDrawings.currentIndex()+1, False)

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

    @Slot(int)
    def handle_spin_random_value_changed(self, value):
        self.put_oxides(self.ui.entryVMD.text())

    @Slot(str)
    def handle_entry_selection_changed(self, text):
        self.put_oxides(text)

    def put_oxides(self, expr):
        if self.ui.comboDrawings.currentIndex() == -1:
            return
        self.manage_duplicates_for_deletion(self.ui.comboDrawings.currentIndex()+1, False)

        fraction_oxidation = self.ui.spinRandom.value()/100
        plate = self.plates[self.ui.comboDrawings.currentIndex()]
        plate.remove_oxides()
        
        if not expr: 
            expr = ""

        def evaluate_condition(x, y, z, i_atom, expr):
            if expr == "": 
                return True
            expr = expr.replace('and', ' and ').replace('or', ' or ').replace('not', ' not ')
            return eval(expr, {'x': x, 'y': y, 'z': z, 'index': i_atom, 
                              'and': lambda a, b: a and b, 
                              'or': lambda a, b: a or b, 
                              'not': lambda x: not x})

        try:
            list_carbons_in_expression = []
            for coord in plate.get_carbon_coords():
                x, y, z, _, i_atom = coord
                x, y, z = x * 10, y * 10, z * 10
                if evaluate_condition(x, y, z, i_atom, expr):
                    list_carbons_in_expression.append(coord)
            
            number_total_carbons = len(list_carbons_in_expression)
            number_oxidations_desired = int(number_total_carbons*fraction_oxidation)
            number_oxidations_done = 0

            plate_try= plate.duplicate([0,0,0])
            plate_try.add_oxydation_to_list_of_carbon(list_carbons_in_expression, self.z_mode, self.last_prob_oh)
            max_theorical_oxidations = plate_try.get_oxide_count()

            if(plate_try.get_oxide_count() <= number_oxidations_desired):
                number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(list_carbons_in_expression, self.z_mode, self.last_prob_oh)
            else:
                oxide_new = []
                if(max_theorical_oxidations > number_oxidations_desired):
                    correction_factor = int(fraction_oxidation*self.last_prob_oh*number_oxidations_desired/200)
                    oxide_new = random.sample(list_carbons_in_expression, min(number_oxidations_desired + correction_factor, number_total_carbons))
                    [list_carbons_in_expression.remove(x) for x in oxide_new]
                    number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(oxide_new, self.z_mode, self.last_prob_oh)
                    while(number_oxidations_desired > plate.get_oxide_count()):
                        oxide_new= [random.choice(list_carbons_in_expression)]
                        list_carbons_in_expression.remove(oxide_new[0])
                        number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(oxide_new, self.z_mode, self.last_prob_oh)
                else:
                    number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(list_carbons_in_expression, self.z_mode, self.last_prob_oh)
                
            print(f"Finished with {number_oxidations_done} oxides, that is {number_oxidations_done/number_total_carbons*100:.2f}% of the selected part of the plate"+" "*20, end='\r')

        except Exception as e:
            print("Not valid expression, exc=",e," "*20, end='\r')

        self.update_drawing_area()

    def set_oxide_mode(self, mode):
        self.active_oxide_mode = mode
        self.first_carbon = None

        self.ui.btnAddOH.setChecked(mode == "OH")
        self.ui.btnAddO.setChecked(mode == "O")
        self.ui.btnRemoveOx.setChecked(mode == "Remove")

    def handle_btn_oh_clicked(self):
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


    # ================================
    # Other methods
    # ================================
    def load_css(self):
        bg_color = "#3d3d3d" if self.is_dark_mode else "white"
        widget_bg = "#2a2a2a" if self.is_dark_mode else "#f5f5f5"
        text_color = "white" if self.is_dark_mode else "black"
        ok_btn = "#2e7d32" if self.is_dark_mode else "lightgreen"
        cancel_btn = "#d32f2f" if self.is_dark_mode else "lightcoral"
        btn_bg = "#424242" if self.is_dark_mode else "#e0e0e0"

        style = f"""
            QGraphicsView {{
                background-color: {bg_color};
            }}
            #topRuler, #leftRuler {{
                background-color: {bg_color};
            }}
            QSpinBox, QLineEdit {{
                background-color: {widget_bg};
                color: {text_color};
            }}
            QPushButton#btn_create_ok, #btn_export_ok, #btn_import_ok, #btn_prob_ok {{
                background-color: {ok_btn};
                color: {text_color};
            }}
            QPushButton#btn_create_cancel, #btn_export_cancel, #btn_import_cancel, #btn_prob_cancel {{
                background-color: {cancel_btn};
                color: {text_color};
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text_color};
            }}
        """
        self.setStyleSheet(style)
        self.ui.drawingArea.setStyleSheet(f"background-color: {bg_color};")
        self.ui.topRuler.setStyleSheet(f"background-color: {bg_color};")
        self.ui.leftRuler.setStyleSheet(f"background-color: {bg_color};")
        
        self.ui.comboDrawings.setStyleSheet(f"background-color: {btn_bg};")

        self.ui.centralwidget.setStyleSheet(f"background-color: {bg_color};")
        self.ui.topToolBar.setStyleSheet(f"background-color: {bg_color};")
        self.ui.bottomBar.setStyleSheet(f"background-color: {bg_color};")

        self.ui.labelOxidation.setStyleSheet(f"color: {text_color};")
        self.ui.labelRandom.setStyleSheet(f"color: {text_color};")
        self.ui.labelVMD.setStyleSheet(f"color: {text_color};")
        self.ui.labelManual.setStyleSheet(f"color: {text_color};")
        self.ui.labelWhere.setStyleSheet(f"color: {text_color};")

    def manage_duplicates_for_deletion(self, index, index_would_be_removed):
        if index in self.plates_corresponding_to_duplicates[0]:
            index_in_list = self.plates_corresponding_to_duplicates[0].index(index)
            self.plates_corresponding_to_duplicates[0].pop(index_in_list)
            self.plates_corresponding_to_duplicates[1].pop(index_in_list)
        elif index in self.plates_corresponding_to_duplicates[1]:
            indexes_in_list = []
            for i in range(len(self.plates_corresponding_to_duplicates[1])):
                if self.plates_corresponding_to_duplicates[1][i] == index:
                    indexes_in_list.append(i)

            if len(indexes_in_list) == 1:
                self.plates_corresponding_to_duplicates[0].pop(indexes_in_list[0])
                self.plates_corresponding_to_duplicates[1].pop(indexes_in_list[0])
            else:
                new_base = self.plates_corresponding_to_duplicates[0][indexes_in_list[0]]
                for i in range(1, len(indexes_in_list)):
                    self.plates_corresponding_to_duplicates[1][indexes_in_list[i]] = new_base
                self.plates_corresponding_to_duplicates[0].pop(indexes_in_list[0])
                self.plates_corresponding_to_duplicates[1].pop(indexes_in_list[0])
        else:
            return
        
        if index_would_be_removed:
            for i in range(len(self.plates_corresponding_to_duplicates[0])):
                for j in range(2):
                    if self.plates_corresponding_to_duplicates[j][i] > index:
                        self.plates_corresponding_to_duplicates[j][i] -= 1
