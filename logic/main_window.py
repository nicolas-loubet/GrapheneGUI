import os
import random
import threading
import math
from pathlib import Path
from logic.other_dialogs import CreateDialog, DuplicateDialog
from logic.graphene import Graphene, generatePatterns
from logic.renderer import Renderer
from logic.export_formats import writeGRO, writeXYZ, writeTOP, writePDB, writeMOL2
from logic.import_formats import readGRO, readXYZ, readPDB, readMOL2
from PySide6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox,
    QGraphicsScene, QGraphicsPixmapItem, QWidget, QDialog)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap, QPainter, QPaintEvent
from ui.main_ui import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        
        self.is_dark_mode = False
        self.active_oxide_mode = None
        self.first_carbon = None
        self.z_mode = 2  # 0: z+, 1: z-, 2: z±
        self.last_prob_oh = 50
        self.last_prob_o = 50
        self.plates = []
        self.plates_corresponding_to_duplicates = [[], []]  # [duplicates, bases]
        
        # Subclasificar rulers para manejar pintura en paintEvent
        is_dark_mode_func = lambda: self.is_dark_mode

        # Reemplaza los placeholders del .ui manteniendo parent, geometry y objectName
        def replace_placeholder_with_custom(placeholder_name, cls):
            placeholder = getattr(self.ui, placeholder_name)
            parent = placeholder.parent()
            geom = placeholder.geometry()
            obj_name = placeholder.objectName()

            # Esconder y eliminar el placeholder original (libera el espacio en la UI)
            placeholder.hide()
            placeholder.deleteLater()

            # Crear nuevo widget en el mismo lugar
            new_w = cls(is_dark_mode_func, parent)
            new_w.setObjectName(obj_name)
            new_w.setGeometry(geom)
            new_w.show()

            # Asignarlo a self.ui para mantener la compatibilidad en el resto del código
            setattr(self.ui, placeholder_name, new_w)
            return new_w
        
        
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
        
        self.destroyed.connect(self.handle_main_window_destroy)
        self.scene.mousePressEvent = self.handle_drawing_area_clicked

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

    def handle_main_window_destroy(self):
        print("Exiting...")
        print("Thanks for using Graphene-GUI")
        print("Please cite: No cite yet, stay in touch!")

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
            
            if dialog.radio_btn_absolute_pos.isChecked():  # Corregido: dialog en lugar de self
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
        dialog = ImportDialog(self)
        if dialog.exec() != QDialog.Accepted: return
        
        file_name = dialog.fileDialog.selectedFiles()[0]
        ext = os.path.splitext(file_name)[1].lower()
        try:
            if ext == ".gro":
                new_plates = readGRO(file_name)
            elif ext == ".xyz":
                new_plates = readXYZ(file_name)
            elif ext == ".mol2":
                new_plates = readMOL2(file_name)
            elif ext == ".pdb":
                new_plates = readPDB(file_name)
            else:
                raise ValueValue(f"Not supported file extension: {ext}")
                
            for plate in new_plates:
                self.plates.append(plate)
                idx = len(self.plates)
                self.ui.comboDrawings.addItem(f"Plate {idx}")
                print(f"Importing coords: Plate {idx}")

            if new_plates:
                self.ui.comboDrawings.setCurrentIndex(len(self.plates)-1)
                self.buttons_that_depend_of_having_a_plate(True)
                self.update_drawing_area()

            print(f"{len(new_plates)} plate(s) imported from {file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error reading file", str(e))
            return

    @Slot()
    def handle_btn_export_clicked(self):
        dialog = ExportDialog(self)
        if dialog.exec() != QDialog.Accepted: return
        
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, 
            "Export File", 
            "", 
            "GRO Files (*.gro);;PDB Files (*.pdb);;XYZ Files (*.xyz);;MOL2 Files (*.mol2);;TOP Files (*.top)"
        )
        
        if not file_name: return
        if '.' not in file_name: file_name += ".gro"

        if os.path.exists(file_name):
            reply = QMessageBox.question(
                self,
                "File exists",
                f"Do you want to overwrite {file_name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        if file_name.endswith(".gro"):
            writeGRO(file_name, self.plates)
        elif file_name.endswith(".pdb"):
            writePDB(file_name, self.plates)
        elif file_name.endswith(".xyz"):
            writeXYZ(file_name, self.plates)
        elif file_name.endswith(".mol2"):
            writeMOL2(file_name, self.plates)
        elif file_name.endswith(".top"):
            factor = dialog.spin_scale.value()/100.0  # Corregido: dialog en lugar de self (asumiendo que está en ExportDialog)
            QMessageBox.information(self, "Exporting topology", "Exporting topology...")
            
            def export_top_and_close():
                writeTOP(file_name, self.plates, factor, self.plates_corresponding_to_duplicates)
                QMessageBox.information(self, "Export Complete", "Topology export completed")
            
            threading.Thread(target=export_top_and_close, daemon=True).start()

    def load_css(self):
        bg_color = "#1e1e1e" if self.is_dark_mode else "white"
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
        # Actualiza rulers para disparar paintEvent
        self.ui.topRuler.update()
        self.ui.leftRuler.update()

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
        self.scene.clear()
        active_index = self.ui.comboDrawings.currentIndex()

        if active_index == -1 or not self.plates or not self.plates[active_index].get_number_atoms():
            # Dibujar fondo si no hay placas
            pixmap = QPixmap("ui/img/background.png")
            if not pixmap.isNull():
                pixmap_item = QGraphicsPixmapItem(pixmap.scaled(
                    self.ui.graphicsView.width(), 
                    self.ui.graphicsView.height(),
                    Qt.KeepAspectRatio
                ))
                self.scene.addItem(pixmap_item)
        else:
            # Renderizar la placa actual
            img = self.renderer.render_plate(self.plates[active_index], self.is_dark_mode)
            pixmap = QPixmap.fromImage(img)
            self.scene.addPixmap(pixmap)

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
            
            number_oxidations_desired = int(len(list_carbons_in_expression)*fraction_oxidation)
            
            oxide_new = random.sample(list_carbons_in_expression, min(number_oxidations_desired, len(list_carbons_in_expression)))
            plate.add_oxydation_to_list_of_carbon(oxide_new, self.z_mode, self.last_prob_oh)
            print(f"Finished with {len(oxide_new)} new oxides")

        except Exception as e:
            print("Not valid expression, exc=", e)

        self.update_drawing_area()

    def set_oxide_mode(self, mode):
        self.active_oxide_mode = mode
        self.first_carbon = None

        self.ui.btnAddOH.setChecked(mode == "OH")
        self.ui.btnAddO.setChecked(mode == "O")
        self.ui.btnRemoveOx.setChecked(mode == "Remove")

    @Slot()
    def handle_btn_oh_clicked(self):
        if self.ui.btnAddOH.isChecked():
            self.set_oxide_mode("OH")
        else:
            self.set_oxide_mode(None)

    @Slot()
    def handle_btn_o_clicked(self):
        if self.ui.btnAddO.isChecked():
            self.set_oxide_mode("O")
        else:
            self.set_oxide_mode(None)

    @Slot()
    def handle_btn_remove_ox_clicked(self):
        if self.ui.btnRemoveOx.isChecked():
            self.set_oxide_mode("Remove")
        else:
            self.set_oxide_mode(None)

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

    @Slot(float)
    def handle_spin_prob_oh_changed(self, value):
        self.spin_prob_o.setValue(100 - value)

    @Slot(float)
    def handle_spin_prob_o_changed(self, value):
        self.spin_prob_oh.setValue(100 - value)

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
