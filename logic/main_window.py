import os
import random
import threading
import math
from logic.graphene import Graphene, generatePatterns
from logic.renderer import Renderer
from logic.export_formats import writeGRO, writeXYZ, writeTOP, writePDB, writeMOL2
from logic.import_formats import readGRO, readXYZ, readPDB, readMOL2
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PySide6.QtCore import Qt, Slot, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QPixmap, QImage
from PySide6.QtUiTools import QUiLoader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loadUi("main.ui", self)
        
        # Conectar señales
        self.setup_connections()
        
        # Inicializar variables de estado
        self.is_dark_mode = False
        self.active_oxide_mode = None
        self.first_carbon = None
        self.z_mode = 2  # 0: z+, 1: z-, 2: z±
        self.last_prob_oh = 50
        self.last_prob_o = 50
        self.plates = []
        self.plates_corresponding_to_duplicates = [[], []]  # [indices_duplicados, indices_base]
        
        # Configurar renderizador
        self.renderer = Renderer()
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        
        # Configurar modo inicial
        self.buttons_that_depend_of_having_a_plate(False)
        self.radioZpm.setChecked(True)

        self.renderer = Renderer(
            drawing_area=self.graphicsView,
            ruler_x=self.topRuler,
            ruler_y=self.leftRuler,
            plates=self.plates,
            cb_plates=self.comboDrawings,
            is_dark_mode_func=lambda: self.is_dark_mode
        )
    
    def loadUi(self, ui_file, parent):
        loader = QUiLoader()
        ui = loader.load(ui_file, parent)
        parent.setCentralWidget(ui)

    def setup_connections(self):
        # Conectar señales de botones
        self.btnCreate.clicked.connect(self.on_btn_create_clicked)
        self.comboDrawings.currentIndexChanged.connect(self.on_cb_plates_changed)
        self.btnDuplicate.clicked.connect(self.on_btn_duplicate_clicked)
        self.btnDelete.clicked.connect(self.on_btn_delete_clicked)
        self.btnImport.clicked.connect(self.on_btn_import_clicked)
        self.btnExport.clicked.connect(self.on_btn_export_clicked)
        self.btnTheme.clicked.connect(self.on_btn_dark_light_mode_clicked)
        self.btnReduceAll.clicked.connect(self.on_btn_reduce_clicked)
        self.btnChangeProb.clicked.connect(self.on_btn_change_prob_clicked)
        self.spinRandom.valueChanged.connect(self.on_spin_random_value_changed)
        self.entryVMD.textChanged.connect(self.on_entry_selection_changed)
        self.btnAddOH.clicked.connect(self.on_btn_oh_clicked)
        self.btnAddO.clicked.connect(self.on_btn_o_clicked)
        self.btnRemoveOx.clicked.connect(self.on_btn_remove_ox_clicked)
        
        # Conectar señales de radio buttons
        self.radioZp.toggled.connect(lambda: self.on_radio_toggled(self.radioZp))
        self.radioZm.toggled.connect(lambda: self.on_radio_toggled(self.radioZm))
        self.radioZpm.toggled.connect(lambda: self.on_radio_toggled(self.radioZpm))
        
        # Conectar evento de cierre
        self.destroyed.connect(self.on_main_window_destroy)
        
        # Conectar evento de clic en el área de dibujo
        self.scene.mousePressEvent = self.on_drawing_area_clicked

    # ================================
    # Funciones de gestión de estado
    # ================================
    def buttons_that_depend_of_having_a_plate(self, active):
        self.btnDuplicate.setEnabled(active)
        self.btnDelete.setEnabled(active)
        self.btnExport.setEnabled(active)
        self.btnReduceAll.setEnabled(active)
        self.btnChangeProb.setEnabled(active)
        self.spinRandom.setEnabled(active)
        self.entryVMD.setEnabled(active)
        self.btnAddOH.setEnabled(active)
        self.btnAddO.setEnabled(active)
        self.btnRemoveOx.setEnabled(active)
        self.radioZpm.setEnabled(active)
        self.radioZp.setEnabled(active)
        self.radioZm.setEnabled(active)

    def on_main_window_destroy(self):
        print("Exiting...")
        print("Thanks for using Graphene-GUI")
        print("Please cite: No cite yet, stay in touch!")

    # ================================
    # Panel superior
    # ================================
    @Slot()
    def on_btn_create_clicked(self):
        self.dialog_create.show()

    @Slot(int)
    def on_cb_plates_changed(self, index):
        self.update_drawing_area()

    @Slot()
    def on_btn_duplicate_clicked(self):
        self.dialog_duplicate.show()

    @Slot()
    def on_btn_delete_clicked(self):
        index = self.comboDrawings.currentIndex()
        if index < 0: return

        self.manage_duplicates_for_deletion(index+1, True)

        self.plates.pop(index)
        self.comboDrawings.clear()
        for i in range(len(self.plates)):
            self.comboDrawings.addItem(f"Plate {i + 1}")
        
        if self.plates:
            self.comboDrawings.setCurrentIndex(0)
        else:
            self.comboDrawings.setCurrentIndex(-1)
            self.buttons_that_depend_of_having_a_plate(False)
            self.spinRandom.setValue(0)
            self.entryVMD.setText("")

        self.update_drawing_area()
        print(f"Plate {index+1} deleted")

    @Slot()
    def on_btn_import_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Import File", "", 
            "All Supported Files (*.gro *.xyz *.mol2 *.pdb);;"
            "GRO Files (*.gro);;XYZ Files (*.xyz);;"
            "MOL2 Files (*.mol2);;PDB Files (*.pdb)"
        )
        
        if file_name:
            self.import_file(file_name)

    @Slot()
    def on_btn_export_clicked(self):
        self.dialog_export.show()

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

    @Slot()
    def on_btn_dark_light_mode_clicked(self):
        self.is_dark_mode = not self.is_dark_mode
        self.load_css()
        self.update_drawing_area()
        print(f"Switched to {'dark' if self.is_dark_mode else 'light'} mode")

    # ================================
    # Área de dibujo
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

    def on_drawing_area_clicked(self, event):
        if self.comboDrawings.currentIndex() == -1 or not self.active_oxide_mode:
            return

        self.manage_duplicates_for_deletion(self.comboDrawings.currentIndex()+1, False)

        plate = self.plates[self.comboDrawings.currentIndex()]
        pos = event.scenePos()
        x, y = pos.x(), pos.y()

        # Convertir coordenadas de píxeles a nm
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
            active_index = self.comboDrawings.currentIndex()

            if active_index == -1 or not self.plates or not self.plates[active_index].get_number_atoms():
                # Dibujar fondo si no hay placas
                pixmap = QPixmap("ui/img/background.png")
                if not pixmap.isNull():
                    pixmap_item = QGraphicsPixmapItem(pixmap.scaled(
                        self.graphicsView.width(), 
                        self.graphicsView.height(),
                        Qt.KeepAspectRatio
                    ))
                    self.scene.addItem(pixmap_item)
            else:
                # Renderizar la placa actual
                img = self.renderer.render_plate(self.plates[active_index], self.is_dark_mode)
                pixmap = QPixmap.fromImage(img)
                self.scene.addPixmap(pixmap)

    # ================================
    # Panel inferior
    # ================================
    @Slot()
    def on_btn_reduce_clicked(self):
        if self.comboDrawings.currentIndex() == -1:
            return
        self.manage_duplicates_for_deletion(self.comboDrawings.currentIndex()+1, False)

        plate = self.plates[self.comboDrawings.currentIndex()]
        plate.remove_oxides()
        self.update_drawing_area()
        self.spinRandom.setValue(0)
        self.entryVMD.setText("")
        print("Oxides removed")

    @Slot()
    def on_btn_change_prob_clicked(self):
        self.last_prob_oh = self.spin_prob_oh.value()
        self.last_prob_o = self.spin_prob_o.value()
        self.dialog_prob.show()

    @Slot(int)
    def on_spin_random_value_changed(self, value):
        self.put_oxides(self.entryVMD.text())

    @Slot(str)
    def on_entry_selection_changed(self, text):
        self.put_oxides(text)

    def put_oxides(self, expr):
        if self.comboDrawings.currentIndex() == -1:
            return
        self.manage_duplicates_for_deletion(self.comboDrawings.currentIndex()+1, False)

        fraction_oxidation = self.spinRandom.value()/100
        plate = self.plates[self.comboDrawings.currentIndex()]
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

        self.btnAddOH.setChecked(mode == "OH")
        self.btnAddO.setChecked(mode == "O")
        self.btnRemoveOx.setChecked(mode == "Remove")

    @Slot()
    def on_btn_oh_clicked(self):
        if self.btnAddOH.isChecked():
            self.set_oxide_mode("OH")
        else:
            self.set_oxide_mode(None)

    @Slot()
    def on_btn_o_clicked(self):
        if self.btnAddO.isChecked():
            self.set_oxide_mode("O")
        else:
            self.set_oxide_mode(None)

    @Slot()
    def on_btn_remove_ox_clicked(self):
        if self.btnRemoveOx.isChecked():
            self.set_oxide_mode("Remove")
        else:
            self.set_oxide_mode(None)

    def on_radio_toggled(self, radio_button):
        if radio_button == self.radioZp and radio_button.isChecked():
            self.z_mode = 0
        elif radio_button == self.radioZm and radio_button.isChecked():
            self.z_mode = 1
        elif radio_button == self.radioZpm and radio_button.isChecked():
            self.z_mode = 2

    # ================================
    # Diálogos
    # ================================
    @Slot()
    def on_btn_create_ok_clicked(self):
        width = self.spin_width.value()
        height = self.spin_height.value()
        center_x = self.spin_center_x.value()
        center_y = self.spin_center_y.value()
        center_z = self.spin_center_z.value()
        factor = self.spin_scale.value()/100.0

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

        self.comboDrawings.addItem(f"Plate {len(self.plates)}")
        self.comboDrawings.setCurrentIndex(len(self.plates) - 1)

        self.update_drawing_area()
        self.buttons_that_depend_of_having_a_plate(True)
        print(f"Coords drawn: Plate {len(self.plates)}")

    @Slot()
    def on_btn_create_cancel_clicked(self):
        self.dialog_create.hide()

    def import_file(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".gro":
                new_plates = readGRO(filename)
            elif ext == ".xyz":
                new_plates = readXYZ(filename)
            elif ext == ".mol2":
                new_plates = readMOL2(filename)
            elif ext == ".pdb":
                new_plates = readPDB(filename)
            else:
                raise ValueError(f"Not supported file extension: {ext}")
        except Exception as e:
            QMessageBox.critical(self, "Error reading file", str(e))
            return

        for plate in new_plates:
            self.plates.append(plate)
            idx = len(self.plates)
            self.comboDrawings.addItem(f"Plate {idx}")
            print(f"Importing coords: Plate {idx}")

        if new_plates:
            self.comboDrawings.setCurrentIndex(len(self.plates)-1)
            self.buttons_that_depend_of_having_a_plate(True)
            self.update_drawing_area()

        print(f"{len(new_plates)} plate(s) imported from {filename}")

    @Slot()
    def on_btn_import_cancel_clicked(self):
        self.dialog_import.hide()

    @Slot()
    def on_btn_export_ok_clicked(self):
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, 
            "Export File", 
            "", 
            "GRO Files (*.gro);;PDB Files (*.pdb);;XYZ Files (*.xyz);;MOL2 Files (*.mol2);;TOP Files (*.top)"
        )
        
        if not file_name:
            return

        if '.' not in file_name:
            file_name += ".gro"

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
            factor = self.spin_scale.value()/100.0
            QMessageBox.information(self, "Exporting topology", "Exporting topology...")
            
            def export_top_and_close():
                writeTOP(file_name, self.plates, factor, self.plates_corresponding_to_duplicates)
                QMessageBox.information(self, "Export Complete", "Topology export completed")
            
            threading.Thread(target=export_top_and_close, daemon=True).start()

        self.dialog_export.hide()

    @Slot()
    def on_btn_export_cancel_clicked(self):
        self.dialog_export.hide()

    @Slot(float)
    def on_spin_prob_oh_changed(self, value):
        self.spin_prob_o.setValue(100 - value)

    @Slot(float)
    def on_spin_prob_o_changed(self, value):
        self.spin_prob_oh.setValue(100 - value)

    @Slot()
    def on_btn_prob_ok_clicked(self):
        self.last_prob_oh = self.spin_prob_oh.value()
        self.last_prob_o = self.spin_prob_o.value()
        self.dialog_prob.hide()

    @Slot()
    def on_btn_prob_cancel_clicked(self):
        self.spin_prob_oh.setValue(self.last_prob_oh)
        self.spin_prob_o.setValue(self.last_prob_o)
        self.dialog_prob.hide()

    @Slot()
    def on_btn_duplicate_ok_clicked(self):
        index_base = self.comboDrawings.currentIndex()+1
        
        plate = self.plates[self.comboDrawings.currentIndex()]
        translation = [
            self.spin_duplicate_x.value(),
            self.spin_duplicate_y.value(),
            self.spin_duplicate_z.value()
        ]
        for i in range(3): 
            translation[i] *= .1  # Change to nm
        
        if self.radio_btn_absolute_pos.isChecked():
            plate_actual_center = plate.get_geometric_center()
            for i in range(3):
                translation[i] -= plate_actual_center[i]

        self.plates.append(plate.duplicate(translation))

        while(index_base in self.plates_corresponding_to_duplicates[0]):
            index_in_list = self.plates_corresponding_to_duplicates[0].index(index_base)
            index_base = self.plates_corresponding_to_duplicates[1][index_in_list]
        
        self.plates_corresponding_to_duplicates[0].append(len(self.plates))
        self.plates_corresponding_to_duplicates[1].append(index_base)

        self.comboDrawings.addItem(f"Plate {len(self.plates)}")
        print(f"Duplicate added: Plate {len(self.plates)}")
        self.comboDrawings.setCurrentIndex(len(self.plates)-1)
        self.dialog_duplicate.hide()

    @Slot()
    def on_btn_duplicate_cancel_clicked(self):
        self.dialog_duplicate.hide()

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
