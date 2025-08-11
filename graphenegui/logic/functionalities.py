import random
import math
import threading
from .graphene import Graphene, generatePatterns
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QFileDialog
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
        x, y, z, _, i_atom = coord
        x, y, z = x * 10, y * 10, z * 10
        if evaluate_condition(x, y, z, i_atom, expr):
            list_carbons_in_expression.append(coord)

def make_oxidations(max_theorical_oxidations, number_oxidations_desired, plate, main_window, list_carbons_in_expression, number_total_carbons, number_oxidations_done, fraction_oxidation):
    oxide_new = []
    if(max_theorical_oxidations > number_oxidations_desired):
        correction_factor = int(fraction_oxidation*main_window.last_prob_oh*number_oxidations_desired/200)
        oxide_new = random.sample(list_carbons_in_expression, min(number_oxidations_desired + correction_factor, number_total_carbons))
        [list_carbons_in_expression.remove(x) for x in oxide_new]
        number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(oxide_new, main_window.z_mode, main_window.last_prob_oh)
        while(number_oxidations_desired > plate.get_oxide_count()):
            oxide_new= [random.choice(list_carbons_in_expression)]
            list_carbons_in_expression.remove(oxide_new[0])
            number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(oxide_new, main_window.z_mode, main_window.last_prob_oh)
    else:
        number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(list_carbons_in_expression, main_window.z_mode, main_window.last_prob_oh)

def put_oxides(main_window, expr):
    if main_window.ui.comboDrawings.currentIndex() == -1: return
    main_window.manage_duplicates_for_deletion(main_window.ui.comboDrawings.currentIndex()+1, False)

    fraction_oxidation = main_window.ui.spinRandom.value()/100
    plate = main_window.plates[main_window.ui.comboDrawings.currentIndex()]
    plate.remove_oxides()
    
    if not expr: expr = ""

    try:
        list_carbons_in_expression = get_list_carbons_in_expr(plate, expr)
        
        number_total_carbons = len(list_carbons_in_expression)
        number_oxidations_desired = int(number_total_carbons*fraction_oxidation)
        number_oxidations_done = 0

        plate_try= plate.duplicate([0,0,0])
        plate_try.add_oxydation_to_list_of_carbon(list_carbons_in_expression, main_window.z_mode, main_window.last_prob_oh)
        max_theorical_oxidations = plate_try.get_oxide_count()

        if(plate_try.get_oxide_count() <= number_oxidations_desired):
            number_oxidations_done+= plate.add_oxydation_to_list_of_carbon(list_carbons_in_expression, main_window.z_mode, main_window.last_prob_oh)
        else:
            make_oxidations(max_theorical_oxidations, number_oxidations_desired, plate, main_window, list_carbons_in_expression, number_total_carbons, number_oxidations_done, fraction_oxidation)
            
        print(f"Finished with {number_oxidations_done} oxides, that is {number_oxidations_done/number_total_carbons*100:.2f}% of the selected part of the plate")

    except Exception as e:
        print("Not valid expression, exc=",e," "*20, end='\r')

    main_window.update_drawing_area()


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

    main_window.load_css()
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

def export_file(main_window):
    filters = ("All Files (*);;GRO Files (*.gro);;PDB Files (*.pdb);;XYZ Files (*.xyz);;MOL2 Files (*.mol2);;TOP Files (*.top);;")
    file_name, selected_filter = QFileDialog.getSaveFileName(main_window, "Export File", "", filters)

    if not file_name: return

    ext_map = {"GRO":".gro", "PDB":".pdb", "XYZ":".xyz", "MOL2":".mol2", "TOP":".top"}
    if '.' not in file_name:
        for key, ext in ext_map.items():
            if key in selected_filter:
                file_name += ext
                break

    if file_name.endswith(".gro"):
        writeGRO(file_name, main_window.plates)
    elif file_name.endswith(".pdb"):
        writePDB(file_name, main_window.plates)
    elif file_name.endswith(".xyz"):
        writeXYZ(file_name, main_window.plates)
    elif file_name.endswith(".mol2"):
        writeMOL2(file_name, main_window.plates)
    elif file_name.endswith(".top"):
        factor = main_window.spin_scale.value() / 100.0
        QMessageBox.information(main_window, "Exporting topology", "Exporting topology...")

        def export_top_and_close():
            writeTOP(file_name, main_window.plates, factor, main_window.plates_corresponding_to_duplicates)
            QMessageBox.information(main_window, "Export Complete", "Topology export completed")

        threading.Thread(target=export_top_and_close, daemon=True).start()

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

    main_window.manage_duplicates_for_deletion(index+1, True)

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
    