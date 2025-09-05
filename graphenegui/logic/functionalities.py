import random
import math
import numpy as np
from .graphene import Graphene, generatePatterns
from PySide6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal, QObject
from .import_formats import readGRO, readXYZ, readPDB, readMOL2
from .export_formats import writeGRO, writeXYZ, writeTOP, writePDB, writeMOL2

# ================================
# General
# ================================

def load_css(main_window):
    bg_color = "#3d3d3d" if main_window.is_dark_mode else "white"
    widget_bg = "#2a2a2a" if main_window.is_dark_mode else "#f5f5f5"
    text_color = "white" if main_window.is_dark_mode else "black"
    ok_btn = "#2e7d32" if main_window.is_dark_mode else "lightgreen"
    cancel_btn = "#d32f2f" if main_window.is_dark_mode else "lightcoral"
    btn_bg = "#424242" if main_window.is_dark_mode else "#e0e0e0"

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
    main_window.setStyleSheet(style)
    main_window.ui.drawingArea.setStyleSheet(f"background-color: {bg_color};")
    main_window.ui.topRuler.setStyleSheet(f"background-color: {bg_color};")
    main_window.ui.leftRuler.setStyleSheet(f"background-color: {bg_color};")
    
    main_window.ui.comboDrawings.setStyleSheet(f"background-color: {btn_bg};")

    main_window.ui.centralwidget.setStyleSheet(f"background-color: {bg_color};")
    main_window.ui.topToolBar.setStyleSheet(f"background-color: {bg_color};")
    main_window.ui.bottomBar.setStyleSheet(f"background-color: {bg_color};")

    main_window.ui.labelOxidation.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelRandom.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelVMD.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelManual.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelWhere.setStyleSheet(f"color: {text_color};")

def manage_duplicates_for_deletion(main_window, index, index_would_be_removed):
    if index in main_window.plates_corresponding_to_duplicates[0]:
        index_in_list = main_window.plates_corresponding_to_duplicates[0].index(index)
        main_window.plates_corresponding_to_duplicates[0].pop(index_in_list)
        main_window.plates_corresponding_to_duplicates[1].pop(index_in_list)
    elif index in main_window.plates_corresponding_to_duplicates[1]:
        indexes_in_list = []
        for i in range(len(main_window.plates_corresponding_to_duplicates[1])):
            if main_window.plates_corresponding_to_duplicates[1][i] == index:
                indexes_in_list.append(i)

        if len(indexes_in_list) == 1:
            main_window.plates_corresponding_to_duplicates[0].pop(indexes_in_list[0])
            main_window.plates_corresponding_to_duplicates[1].pop(indexes_in_list[0])
        else:
            new_base = main_window.plates_corresponding_to_duplicates[0][indexes_in_list[0]]
            for i in range(1, len(indexes_in_list)):
                main_window.plates_corresponding_to_duplicates[1][indexes_in_list[i]] = new_base
            main_window.plates_corresponding_to_duplicates[0].pop(indexes_in_list[0])
            main_window.plates_corresponding_to_duplicates[1].pop(indexes_in_list[0])
    else:
        return
    
    if index_would_be_removed:
        for i in range(len(main_window.plates_corresponding_to_duplicates[0])):
            for j in range(2):
                if main_window.plates_corresponding_to_duplicates[j][i] > index:
                    main_window.plates_corresponding_to_duplicates[j][i] -= 1


# ================================
# Oxidation
# ================================

def evaluate_condition(x, y, z, i_atom, expr):
    if expr == "": return True
    expr = expr.replace('and', ' and ').replace('or', ' or ').replace('not', ' not ')
    return eval(expr, {'x': x, 'y': y, 'z': z, 'index': i_atom, 'and': lambda a, b: a and b, 'or': lambda a, b: a or b, 'not': lambda x: not x})

def get_list_carbons_in_expr(plate, expr):
    list_carbons_in_expression = []
    for coord in plate.get_carbon_coords():
        x, y, z, _, i_atom = coord[:5]
        x, y, z = x * 10, y * 10, z * 10
        if evaluate_condition(x, y, z, i_atom, expr):
            list_carbons_in_expression.append(coord)
    return list_carbons_in_expression

def select_atoms_expr(main_window, expr):
    if main_window.ui.comboDrawings.currentIndex() == -1: return None
    manage_duplicates_for_deletion(main_window, main_window.ui.comboDrawings.currentIndex()+1, False)
    plate= main_window.plates[main_window.ui.comboDrawings.currentIndex()]

    fraction_oxidation= main_window.ui.spinRandom.value() / 100
    if not expr: expr= ""

    try:
        list_carbons_in_expression= get_list_carbons_in_expr(plate, expr)
        number_total_carbons= len(list_carbons_in_expression)
        number_oxidations_desired= int(number_total_carbons * fraction_oxidation)

        if number_total_carbons == 0 or number_oxidations_desired == 0: return None

        plate_try= plate.duplicate([0, 0, 0])
        plate_try.add_oxydation_to_list_of_carbon(list_carbons_in_expression, main_window.z_mode, main_window.last_prob_oh)
        max_theorical_oxidations= plate_try.get_oxide_count()

        if max_theorical_oxidations <= number_oxidations_desired:
            selected_atoms= list_carbons_in_expression
        else:
            correction_factor= int(fraction_oxidation * main_window.last_prob_oh * number_oxidations_desired / 200)
            selected_atoms= random.sample(list_carbons_in_expression, min(number_oxidations_desired + correction_factor, number_total_carbons))

        return selected_atoms

    except Exception as e:
        print("Not valid expression, exc=", e, " "*20, end="\r")
        return None

def put_oxides(main_window, list_carbons):
    if not list_carbons: return 0
    if main_window.ui.comboDrawings.currentIndex() == -1: return 0

    plate= main_window.plates[main_window.ui.comboDrawings.currentIndex()]
    number_oxidations_done= plate.add_oxydation_to_list_of_carbon(list_carbons, main_window.z_mode, main_window.last_prob_oh)

    main_window.update_drawing_area()
    print(f"Finished with {number_oxidations_done} oxides, that is {plate.get_oxide_count()/plate.get_number_atoms()*100:.2f}% of the selected part of the plate")
    return number_oxidations_done


# ================================
# Top panel
# ================================
def create_plate(dialog, main_window):
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
        QMessageBox.critical(main_window, "Too large", f"The number of atoms is too large ({max_atoms}). Reduce the width or height.")
        return

    plate = Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor)
    main_window.plates.append(plate)

    main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")
    main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)

    load_css(main_window)
    main_window.update_drawing_area()
    main_window.buttons_that_depend_of_having_a_plate(True)
    print(f"Coords drawn: Plate {len(main_window.plates)}")

def import_file(ext, file_name, main_window):
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
        main_window.plates.append(plate)
        idx = len(main_window.plates)
        main_window.ui.comboDrawings.addItem(f"Plate {idx}")
        print(f"Importing coords: Plate {idx}")

    if new_plates:
        main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)
        main_window.buttons_that_depend_of_having_a_plate(True)
        main_window.update_drawing_area()

    print(f"{len(new_plates)} plate(s) imported from {file_name}")

class ExportTopWorker(QObject):
    finished = Signal()
    progress = Signal(float)

    def __init__(self, file_name, plates, plates_duplicates):
        super().__init__()
        self.file_name = file_name
        self.plates = plates
        self.plates_duplicates = plates_duplicates

    def run(self):
        def progress_callback(frac):
            self.progress.emit(frac)

        writeTOP(self.file_name, self.plates, self.plates_duplicates, progress_callback)
        self.finished.emit()

def export_top(main_window, file_name, plates):
    progress_dialog = QProgressDialog("Exportando archivo TOP...", None, 0, 100, main_window)
    progress_dialog.setWindowTitle("Exportando...")
    progress_dialog.setWindowModality(Qt.ApplicationModal)
    progress_dialog.setCancelButton(None)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.setValue(0)
    progress_dialog.show()

    worker = ExportTopWorker(file_name, plates, main_window.plates_corresponding_to_duplicates)

    worker.progress.connect(lambda frac: progress_dialog.setValue(int(frac * 100)))
    worker.finished.connect(progress_dialog.close)

    thread = QThread()
    worker.moveToThread(thread)
    worker.finished.connect(thread.quit)
    thread.started.connect(worker.run)

    def cleanup():
        thread.wait()
        del main_window._export_thread
        del main_window._export_worker
        del main_window._export_progress_dialog

    thread.finished.connect(cleanup)

    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()

    main_window._export_thread = thread
    main_window._export_worker = worker
    main_window._export_progress_dialog = progress_dialog

def export_file(main_window):
    filters = ("All Files (*);;GRO Files (*.gro);;PDB Files (*.pdb);;XYZ Files (*.xyz);;MOL2 Files (*.mol2);;TOP Files (*.top);;")
    file_name, selected_filter = QFileDialog.getSaveFileName(main_window, "Export File", "", filters)

    if not file_name:
        return

    plates = main_window.plates

    ext_map = {"GRO": ".gro", "PDB": ".pdb", "XYZ": ".xyz", "MOL2": ".mol2", "TOP": ".top"}
    if '.' not in file_name:
        for key, ext in ext_map.items():
            if key in selected_filter:
                file_name += ext
                break

    if file_name.endswith(".top"):
        export_top(main_window, file_name, plates)
    elif file_name.endswith(".gro"):
        writeGRO(file_name, plates)
    elif file_name.endswith(".pdb"):
        writePDB(file_name, plates)
    elif file_name.endswith(".xyz"):
        writeXYZ(file_name, plates)
    elif file_name.endswith(".mol2"):
        writeMOL2(file_name, plates)
    else:
        print("Unsupported file extension")

def create_duplicate(main_window, dialog):
    index_base = main_window.ui.comboDrawings.currentIndex()+1

    plate = main_window.plates[main_window.ui.comboDrawings.currentIndex()]
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

    main_window.plates.append(plate.duplicate(translation))

    while(index_base in main_window.plates_corresponding_to_duplicates[0]):
        index_in_list = main_window.plates_corresponding_to_duplicates[0].index(index_base)
        index_base = main_window.plates_corresponding_to_duplicates[1][index_in_list]
    
    main_window.plates_corresponding_to_duplicates[0].append(len(main_window.plates))
    main_window.plates_corresponding_to_duplicates[1].append(index_base)

    main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")
    print(f"Duplicate added: Plate {len(main_window.plates)}")
    main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates)-1)

def delete_actual_plate(main_window):
    index = main_window.ui.comboDrawings.currentIndex()
    if index < 0: return

    manage_duplicates_for_deletion(main_window, index+1, True)

    main_window.plates.pop(index)
    main_window.ui.comboDrawings.clear()
    for i in range(len(main_window.plates)):
        main_window.ui.comboDrawings.addItem(f"Plate {i + 1}")
    
    if main_window.plates:
        main_window.ui.comboDrawings.setCurrentIndex(0)
    else:
        main_window.ui.comboDrawings.setCurrentIndex(-1)
        main_window.buttons_that_depend_of_having_a_plate(False)
        main_window.ui.spinRandom.setValue(0)
        main_window.ui.entryVMD.setText("")

    main_window.update_drawing_area()
    print(f"Plate {index+1} deleted")

def remove_overlapping_atoms(atoms):
    to_remove_list= []
    for i in range(len(atoms)):
        for j in range(i+1, len(atoms)):
            x1,y1,z1 = atoms[i][:3]
            x2,y2,z2 = atoms[j][:3]
            if np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) < .02:
                to_remove_list.append(j)
    print(f"Removed {len(to_remove_list)} overlapping atoms")
    return np.delete(atoms, to_remove_list, axis=0)

def roll_atoms_as_CNT(atoms, roll_vec, center=[0,0,0]):
    atoms= np.array(atoms, dtype=object)
    ux, uy= roll_vec
    L= np.sqrt(ux**2 + uy**2)
    if L == 0: raise ValueError("The rolling vector cannot be (0,0).")

    R= L / (2 * np.pi)

    e_u, e_v= np.array([ux,uy])/L, np.array([-uy,ux])/L

    xy= np.array(atoms[:,:2].tolist(), dtype=float)
    atom_z= np.array(atoms[:,2].tolist(), dtype=float)

    is_carbon= np.array([str(a).startswith("C") for a in atoms[:,3]])
    z_ref= np.mean(atom_z[is_carbon])

    delta_z= atom_z - z_ref

    u,v= np.dot(xy, e_u), np.dot(xy, e_v)
    theta= 2*np.pi * u / L
    R_eff= R - delta_z
    new_x, new_y, new_z= R_eff*np.cos(theta), R_eff*np.sin(theta), v

    new_atoms= atoms.copy()
    for i in range(len(new_atoms)):
        new_atoms[i][0], new_atoms[i][1], new_atoms[i][2]= new_x[i], new_y[i], new_z[i]
    
    carbons= new_atoms[is_carbon]
    carbon_coords= np.array([list(c[:3]) for c in carbons], dtype=float)
    new_center= np.mean(carbon_coords, axis=0)
    displacement= new_center - np.array(center)
    
    for i in range(len(new_atoms)):
        new_atoms[i][:3]= np.array(new_atoms[i][:3], dtype=float) - displacement
    
    return remove_overlapping_atoms(new_atoms)
