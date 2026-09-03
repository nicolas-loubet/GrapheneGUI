from PySide6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal, QObject
import yaml
from .graphene import Graphene
from . import core

# ================================
# General
# ================================

def load_css(main_window):
    bg_color= "#3d3d3d" if main_window.is_dark_mode else "white"
    widget_bg= "#2a2a2a" if main_window.is_dark_mode else "#f5f5f5"
    text_color= "white" if main_window.is_dark_mode else "black"
    ok_btn= "#2e7d32" if main_window.is_dark_mode else "lightgreen"
    cancel_btn= "#d32f2f" if main_window.is_dark_mode else "lightcoral"
    btn_bg= "#424242" if main_window.is_dark_mode else "#e0e0e0"

    style= f"""
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

    main_window.ui.comboDrawings.setStyleSheet(f"color: {text_color};")
    main_window.rubberBand.setStyleSheet("QRubberBand { border: 2px solid blue; background: rgba(0, 0, 255, 20); }")

    main_window.ui.labelOxidation.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelRandom.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelVMD.setStyleSheet(f"color: {text_color};")
    main_window.ui.comboCType.setStyleSheet(f"color: {text_color};")

    main_window.ui.labelManual.setStyleSheet(f"color: {text_color};")
    main_window.ui.labelWhere.setStyleSheet(f"color: {text_color};")
    main_window.ui.radioZpm.setStyleSheet(f"color: {text_color};")
    main_window.ui.radioZp.setStyleSheet(f"color: {text_color};")
    main_window.ui.radioZm.setStyleSheet(f"color: {text_color};")

def record_new_oxides(main_window, plate_position, oxide_count_before):
    """Compara oxide_coords antes/después de una acción y graba en el recorder (si la
    placa fue creada vía dialog, ver PlateRegistry/SessionRecorder.has_plate) los
    átomos NUEVOS como un paso 'hard' — exactos, sin importar si vinieron de una
    expresión, un click manual, o una oxidación forzada. Placas no trackeables
    (importadas o duplicadas, ver TODO Etapa 5) se ignoran en silencio."""
    plate_id= main_window.plates.id_at(plate_position)
    if not main_window.session_recorder.has_plate(plate_id): return
    plate= main_window.plates[plate_position]
    new_oxides= plate.get_oxide_coords()[oxide_count_before:]
    oxide_atoms= [[x*10, y*10, z*10, t] for x, y, z, t, *_ in new_oxides]
    if oxide_atoms:
        main_window.session_recorder.record_oxidation_hard(plate_id, oxide_atoms)


# ================================
# Oxidation
# ================================

def evaluate_condition(x, y, z, i_atom, expr):
    return core.evaluate_condition(x, y, z, i_atom, expr)

def get_list_carbons_in_expr(plate, expr):
    return core.get_list_carbons_in_expr(plate, expr)

def select_atoms_expr(main_window, expr):
    if main_window.ui.comboDrawings.currentIndex() == -1: return None
    plate= main_window.plates[main_window.ui.comboDrawings.currentIndex()]

    fraction_oxidation= main_window.ui.spinRandom.value() / 100
    return core.select_atoms(plate, expr, fraction_oxidation, main_window.z_mode, main_window.last_prob_oh)

def put_oxides(main_window, list_carbons):
    if not list_carbons: return 0
    if main_window.ui.comboDrawings.currentIndex() == -1: return 0

    plate_index= main_window.ui.comboDrawings.currentIndex()
    plate= main_window.plates[plate_index]
    oxide_count_before= len(plate.get_oxide_coords())
    number_oxidations_done= core.apply_oxidation(plate, list_carbons, main_window.z_mode, main_window.last_prob_oh)
    record_new_oxides(main_window, plate_index, oxide_count_before)

    main_window.update_drawing_area()
    print(f"Finished with {number_oxidations_done} oxides, that is {plate.get_oxide_count()/plate.get_number_atoms()*100:.2f}% of the selected part of the plate")
    return number_oxidations_done


# ================================
# Top panel
# ================================
def create_plate(dialog, main_window):
    width= dialog.spin_width.value()
    height= dialog.spin_height.value()
    center_x= dialog.spin_center_x.value()
    center_y= dialog.spin_center_y.value()
    center_z= dialog.spin_center_z.value()
    factor= dialog.spin_scale.value()/100.0
    main_window.periodicity_conditions= [dialog.check_pbc_x.isChecked(), dialog.check_pbc_y.isChecked()]
    main_window.renderer.set_periodicity(main_window.periodicity_conditions)

    center_x_nm= center_x / 10
    center_y_nm= center_y / 10
    center_z_nm= center_z / 10

    n_x, n_y= core.compute_plate_grid(width, height, factor)
    fits, max_atoms= core.check_plate_size(n_x, n_y)
    if not fits:
        QMessageBox.critical(main_window, "Too large", f"The number of atoms is too large ({max_atoms}). Reduce the width or height.")
        return

    plate= Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor,
                                        dialog.check_pbc_x.isChecked(), dialog.check_pbc_y.isChecked())
    plate_id= main_window.plates.add(plate)
    main_window.session_recorder.record_plate_created({
        "width": width, "height": height, "factor": factor,
        "center": [center_x, center_y, center_z],
        "periodic_boundary_x": dialog.check_pbc_x.isChecked(),
        "periodic_boundary_y": dialog.check_pbc_y.isChecked(),
    }, name=plate_id)

    main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")
    main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)

    load_css(main_window)
    main_window.update_drawing_area()
    main_window.buttons_that_depend_of_having_a_plate(True)

    if dialog.check_pbc_x.isChecked() or dialog.check_pbc_y.isChecked():
        main_window.ui.btnReduceExternal.setEnabled(False)

    print(f"Coords drawn: Plate {len(main_window.plates)}")

def import_file(ext, file_name, main_window):
    new_plates= core.load_plates_from_file(ext, file_name)

    for plate in new_plates:
        main_window.plates.add(plate)  # importada: no se registra en el recorder, ver TODO Etapa 5
        idx= len(main_window.plates)
        main_window.ui.comboDrawings.addItem(f"Plate {idx}")
        print(f"Importing coords: Plate {idx}")

    if new_plates:
        main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)
        main_window.buttons_that_depend_of_having_a_plate(True)
        main_window.update_drawing_area()

    print(f"{len(new_plates)} plate(s) imported from {file_name}")

class ExportTopWorker(QObject):
    finished= Signal()
    progress= Signal(int)

    def __init__(self, file_name, plates, plates_duplicates, atom_types, periodicity_conditions):
        super().__init__()
        self.file_name= file_name
        self.plates= plates
        self.plates_duplicates= plates_duplicates
        self.atom_types= atom_types
        self.periodicity_conditions= periodicity_conditions

    def run(self):
        def progress_callback(frac):
            self.progress.emit(int(frac*100))

        core.export_plates(self.file_name, self.plates, self.periodicity_conditions,
                            atom_types=self.atom_types, duplicates_list=self.plates_duplicates,
                            progress_callback=progress_callback)
        self.finished.emit()

def export_top(main_window, file_name, plates, periodicity_conditions):
    progress_dialog= QProgressDialog("Exporting TOP file...", None, 0, 100, main_window)
    progress_dialog.setWindowTitle("Exporting...")
    progress_dialog.setWindowModality(Qt.ApplicationModal)
    progress_dialog.setCancelButton(None)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.setValue(0)
    progress_dialog.show()

    worker= ExportTopWorker(file_name, plates, main_window.plates.resolve_duplicate_groups(), main_window.atom_types, periodicity_conditions)

    worker.progress.connect(progress_dialog.setValue, Qt.QueuedConnection)
    worker.finished.connect(progress_dialog.accept, Qt.QueuedConnection)

    thread= QThread()
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

    main_window._export_thread= thread
    main_window._export_worker= worker
    main_window._export_progress_dialog= progress_dialog

def export_file(main_window):
    filters= ("All Files (*);;GRO Files (*.gro);;PDB Files (*.pdb);;XYZ Files (*.xyz);;MOL2 Files (*.mol2);;TOP Files (*.top);;")
    file_name, selected_filter= QFileDialog.getSaveFileName(main_window, "Export File", "", filters)

    if not file_name:
        return

    plates= main_window.plates

    ext_map= {"GRO": ".gro", "PDB": ".pdb", "XYZ": ".xyz", "MOL2": ".mol2", "TOP": ".top"}
    if '.' not in file_name:
        for key, ext in ext_map.items():
            if key in selected_filter:
                file_name += ext
                break

    if file_name.endswith(".top"):
        export_top(main_window, file_name, plates, main_window.periodicity_conditions)
        return

    try:
        core.export_plates(file_name, plates, main_window.periodicity_conditions)
    except ValueError:
        print("Unsupported file extension")

def create_duplicate(main_window, dialog):
    source_position= main_window.ui.comboDrawings.currentIndex()
    source_plate= main_window.plates[source_position]
    source_id= main_window.plates.id_at(source_position)

    translation= core.compute_duplicate_translation(
        dialog.spin_duplicate_x.value(),
        dialog.spin_duplicate_y.value(),
        dialog.spin_duplicate_z.value(),
        dialog.radio_btn_absolute_pos.isChecked(),
        source_plate.get_geometric_center()
    )

    new_plate_id= main_window.plates.add(source_plate.duplicate(translation), duplicate_of=source_id, translation=translation)

    # Etapa 11: el duplicado usa el MISMO id que le asignó el registry como nombre
    # en el recorder — así queda trackeable para ediciones posteriores (oxidar,
    # CNT, etc.) igual que cualquier placa creada de cero. Antes esto no pasaba,
    # y cualquier edición sobre un duplicado se perdía silenciosamente.
    if main_window.session_recorder.has_plate(source_id):
        main_window.session_recorder.record_duplicate(
            source_id,
            [dialog.spin_duplicate_x.value(), dialog.spin_duplicate_y.value(), dialog.spin_duplicate_z.value()],
            dialog.radio_btn_absolute_pos.isChecked(),
            name=new_plate_id,
        )
    # si la fuente no era trackeable (ej. importada), el duplicado tampoco lo es —
    # no tiene sentido grabar un duplicado de algo que no se puede reconstruir

    main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")
    print(f"Duplicate added: Plate {len(main_window.plates)}")
    main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates)-1)

def delete_actual_plate(main_window):
    index= main_window.ui.comboDrawings.currentIndex()
    if index < 0: return

    plate_id= main_window.plates.id_at(index)
    if main_window.session_recorder.has_plate(plate_id):
        main_window.session_recorder.remove_plate(plate_id)
    main_window.plates.remove_at(index)

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
    return core.remove_overlapping_atoms(atoms)

def roll_atoms_as_CNT(atoms, roll_vec, center=[0,0,0]):
    return core.roll_atoms_as_CNT(atoms, roll_vec, center)


# ================================
# Guardar trabajo (Etapa 7)
# ================================
def save_work(main_window):
    """Vuelca la sesión grabada por session_recorder a un YAML reproducible con
    graphene-gui-cli -c archivo.yaml (schema multi-placa de la Etapa 1, que
    cli.py ya sabe leer desde la Etapa 8)."""
    if main_window.session_recorder.is_empty():
        QMessageBox.information(main_window, "Nothing to save",
                                 "There's nothing recorded yet — create a plate first.")
        return

    file_name, _= QFileDialog.getSaveFileName(main_window, "Save Work", "",
                                               "YAML Files (*.yaml *.yml);;All Files (*)")
    if not file_name:
        return
    if not file_name.endswith((".yaml", ".yml")):
        file_name += ".yaml"

    main_window.session_recorder.save(file_name, export_formats=["mol2", "top"],
                                       output_dir="./output", export_name="graphene")

    QMessageBox.information(main_window, "Saved", f"Session saved to:\n{file_name}")
    print(f"Session saved to {file_name}")


def open_work(main_window):
    """Etapa 9 (schema unificado desde la Etapa 11): abre un YAML de sesión y
    reconstruye las placas en la GUI, usando la MISMA función que usa el
    headless (core.build_session_from_config) — no se reimplementa el parseo.

    Cada placa (sea 'create' o 'duplicate_of' — ya no hay distinción de
    trackeabilidad entre las dos) se re-registra en el recorder con un único
    paso 'hard' que refleja el estado final de óxidos (no el historial paso a
    paso original), para que 'Guardar trabajo' siga funcionando después de
    abrir una sesión, y para que se pueda seguir editando cualquier placa —
    incluidos los duplicados — con esas ediciones quedando grabadas."""
    file_name, _= QFileDialog.getOpenFileName(main_window, "Open Work", "",
                                               "YAML Files (*.yaml *.yml);;All Files (*)")
    if not file_name:
        return

    try:
        with open(file_name) as f:
            cfg= yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        QMessageBox.critical(main_window, "Error", f"Couldn't read {file_name}:\n{e}")
        return

    if "plates" not in cfg:
        QMessageBox.critical(main_window, "Error",
                              "This file doesn't look like a multi-plate session YAML (missing 'plates').")
        return

    try:
        plates_by_name, _, _, atom_types, _= core.build_session_from_config(cfg)
    except ValueError as e:
        QMessageBox.critical(main_window, "Error", f"Couldn't load session:\n{e}")
        return

    registry_id_by_config_name= {}

    for plate_cfg in cfg["plates"]:
        name= plate_cfg["name"]
        plate= plates_by_name[name]

        if "duplicate_of" in plate_cfg:
            source_name= plate_cfg["duplicate_of"]
            source_id= registry_id_by_config_name.get(source_name)
            source_plate= plates_by_name[source_name]
            dx, dy, dz= plate_cfg["translation"]
            absolute= plate_cfg.get("absolute", False)
            translation= core.compute_duplicate_translation(dx, dy, dz, absolute, source_plate.get_geometric_center())
            plate_id= main_window.plates.add(plate, duplicate_of=source_id, translation=translation)

            if source_id is not None and main_window.session_recorder.has_plate(source_id):
                main_window.session_recorder.record_duplicate(
                    source_id, plate_cfg["translation"], absolute, name=plate_id)
        else:
            plate_id= main_window.plates.add(plate)
            main_window.session_recorder.record_plate_created(plate_cfg.get("create", {}), name=plate_id)

        registry_id_by_config_name[name]= plate_id

        # Estado final de óxidos como un único step 'hard' — sea placa nueva o
        # duplicado, así 'Guardar trabajo' sigue funcionando después de reabrir.
        if main_window.session_recorder.has_plate(plate_id):
            oxide_coords= plate.get_oxide_coords()
            if oxide_coords:
                oxide_atoms= [[x*10, y*10, z*10, t] for x, y, z, t, *_ in oxide_coords]
                main_window.session_recorder.record_oxidation_hard(plate_id, oxide_atoms)

        main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")

    for name, params in atom_types.items():
        main_window.atom_types[name]= params
        main_window.ui.comboCType.addItem(name)
        main_window.session_recorder.record_atom_type(name, params["epsilon"], params["sigma"])

    if len(main_window.plates) > 0:
        main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)
        main_window.buttons_that_depend_of_having_a_plate(True)
        main_window.update_drawing_area()

    print(f"{len(cfg['plates'])} plate(s) loaded from {file_name}")
