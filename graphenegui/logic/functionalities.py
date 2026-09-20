from PySide6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal, QObject
import yaml
from .graphene import Graphene, DEFAULT_CARBON_TYPE
from .recorder import SessionRecorder
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
    (importadas o duplicadas) se ignoran en silencio."""
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

def remove_oxides_from_selection(main_window, list_carbons):
    if not list_carbons: return 0
    if main_window.ui.comboDrawings.currentIndex() == -1: return 0

    plate_index= main_window.ui.comboDrawings.currentIndex()
    plate= main_window.plates[plate_index]
    plate_id= main_window.plates.id_at(plate_index)
    trackeable= main_window.session_recorder.has_plate(plate_id)

    ya_removidos= set()
    removed_count= 0
    with main_window.session_recorder.batch_action():
        for carbon in list_carbons:
            for ox in plate.get_oxides_for_carbon(carbon):
                if id(ox) in ya_removidos:
                    continue
                ya_removidos.add(id(ox))
                plate.remove_atom_oxide(ox)
                if trackeable:
                    main_window.session_recorder.record_oxidation_removed(plate_id, [ox[0]*10, ox[1]*10, ox[2]*10, ox[3]])
                removed_count+= 1

    if removed_count:
        plate.recheck_ox_indexes()
    main_window.update_drawing_area()
    print(f"{removed_count} atom{'s' if removed_count != 1 else ''} removed from selection "
          f"({len(list_carbons)} carbon{'s' if len(list_carbons) != 1 else ''} checked)")
    return removed_count

def record_carbon_type_change(main_window, plate_position, carbons, new_type):
    """Graba en el recorder (si la placa es trackeable, ver PlateRegistry/
    SessionRecorder.has_plate) un cambio de tipo de carbono YA APLICADO.
    'carbons' son las tuplas completas de Graphene de los carbonos MODIFICADOS
    (sea que vinieran de un click manual o de aplicar a una selección entera)"""
    plate_id= main_window.plates.id_at(plate_position)
    if not main_window.session_recorder.has_plate(plate_id): return
    positions= [[c[0]*10, c[1]*10, c[2]*10] for c in carbons]
    if positions:
        main_window.session_recorder.record_carbon_type(plate_id, positions, new_type)

def apply_ctype_to_selection(main_window, list_carbons, new_type):
    """Botón 'Apply to selection': aplica new_type a TODOS los carbonos de
    list_carbons (selección por expresión o rectángulo, ver
    information_selected_atoms). Filtra de entrada los que ya tienen ese tipo"""
    if not list_carbons: return 0
    if main_window.ui.comboDrawings.currentIndex() == -1: return 0

    plate_index= main_window.ui.comboDrawings.currentIndex()
    plate= main_window.plates[plate_index]
    changed_carbons= [c for c in list_carbons if c[6] != new_type]
    for carbon in changed_carbons:
        plate.set_carbon_type(carbon, new_type)
    record_carbon_type_change(main_window, plate_index, changed_carbons, new_type)

    main_window.update_drawing_area()
    skipped= len(list_carbons) - len(changed_carbons)
    print(f"Set {len(changed_carbons)} carbon(s) to type '{new_type}'"
          f"{f' ({skipped} already had it)' if skipped else ''}")
    return len(changed_carbons)


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
        main_window.plates.add(plate)
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

    if main_window.session_recorder.has_plate(source_id):
        main_window.session_recorder.record_duplicate(
            source_id,
            [dialog.spin_duplicate_x.value(), dialog.spin_duplicate_y.value(), dialog.spin_duplicate_z.value()],
            dialog.radio_btn_absolute_pos.isChecked(),
            name=new_plate_id,
        )

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
        main_window.vmd_debounce_timer.stop()
        main_window.ui.entryVMD.setText("")
        main_window.expr_changed()

    main_window.update_drawing_area()
    print(f"Plate {index+1} deleted")

def remove_overlapping_atoms(atoms):
    return core.remove_overlapping_atoms(atoms)

def roll_atoms_as_CNT(atoms, roll_vec, center=[0,0,0]):
    return core.roll_atoms_as_CNT(atoms, roll_vec, center)


def save_work(main_window):
    if main_window.session_recorder.is_empty():
        QMessageBox.information(main_window, "Nothing to save",
                                 "There's nothing recorded yet — create a plate first.")
        return None

    file_name, _= QFileDialog.getSaveFileName(main_window, "Save Work", "",
                                               "YAML Files (*.yaml *.yml);;All Files (*)")
    if not file_name:
        return None
    if not file_name.endswith((".yaml", ".yml")):
        file_name += ".yaml"

    main_window.session_recorder.save(file_name, export_formats=["mol2", "top"],
                                       output_dir="./output", export_name="graphene")
    main_window.session_recorder.mark_saved()

    QMessageBox.information(main_window, "Saved", f"Session saved to:\n{file_name}")
    print(f"Session saved to {file_name}")
    return file_name


def open_work_with_confirmation(main_window):
    if len(main_window.plates) > 0:
        choice= _ask_add_or_open_new(main_window)
        if choice is None:
            return  # canceló el primer diálogo, no se toca nada
        if choice == "new":
            if main_window.session_recorder.is_modified():
                if not offer_save_before_discarding(main_window):
                    return  # canceló guardar, o canceló el diálogo de guardar
            reset_session(main_window)

    open_work(main_window)

def _ask_add_or_open_new(main_window):
    """Devuelve 'add', 'new', o None (canceló)."""
    msg= QMessageBox(main_window)
    msg.setWindowTitle("Open Work")
    msg.setText("Add the plates from the file to the current session, "
                 "or close the current session and open a new one?")
    btn_add= msg.addButton("Add to current", QMessageBox.ButtonRole.AcceptRole)
    btn_new= msg.addButton("Open new (close current)", QMessageBox.ButtonRole.DestructiveRole)
    msg.addButton(QMessageBox.StandardButton.Cancel)
    msg.exec()
    clicked= msg.clickedButton()
    if clicked is btn_add: return "add"
    if clicked is btn_new: return "new"
    return None

def confirm_close(main_window):
    if not main_window.session_recorder.is_modified():
        return True
    return offer_save_before_discarding(main_window)


def offer_save_before_discarding(main_window):
    msg= QMessageBox(main_window)
    msg.setWindowTitle("Unsaved changes")
    msg.setText("The current session has unsaved changes. Save it before closing?")
    btn_save= msg.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
    btn_discard= msg.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
    msg.addButton(QMessageBox.StandardButton.Cancel)
    msg.exec()
    clicked= msg.clickedButton()
    if clicked is btn_discard:
        return True
    if clicked is btn_save:
        return bool(save_work(main_window))  # False si canceló el diálogo de guardar
    return False  # Cancel

def reset_session(main_window):
    while len(main_window.plates) > 0:
        main_window.plates.remove_at(0)
    main_window.ui.comboDrawings.clear()
    main_window.information_selected_atoms= []
    main_window.renderer.highlighted_atoms= []
    main_window.first_carbon= None
    main_window.set_oxide_mode(None)
    main_window.set_ctype_mode(None)
    main_window.session_recorder= SessionRecorder()
    main_window.atom_types= {DEFAULT_CARBON_TYPE: {"epsilon": 0.359824, "sigma": 3.39967}}
    main_window.current_ctype= DEFAULT_CARBON_TYPE
    main_window.ui.comboCType.clear()
    main_window.ui.comboCType.addItem(DEFAULT_CARBON_TYPE)
    main_window.buttons_that_depend_of_having_a_plate(False)
    main_window.update_drawing_area()


# ================================
# Undo / Redo
# ================================

def _rebuild_plates_from_recorder(main_window):
    cfg= main_window.session_recorder.to_dict()

    while len(main_window.plates) > 0:
        main_window.plates.remove_at(0)
    main_window.ui.comboDrawings.clear()

    if cfg["plates"]:
        plates_by_name, _, _, _, _= core.build_session_from_config(cfg)
        registry_id_by_config_name= {}

        for name, parent_name, translation_raw, absolute, _cnt_vector in core.iter_plate_build_order(cfg):
            plate= plates_by_name[name]
            if parent_name is not None:
                source_id= registry_id_by_config_name[parent_name]
                source_plate= plates_by_name[parent_name]
                dx, dy, dz= translation_raw
                translation= core.compute_duplicate_translation(dx, dy, dz, absolute, source_plate.get_geometric_center())
                plate_id= main_window.plates.add(plate, duplicate_of=source_id, translation=translation)
            else:
                plate_id= main_window.plates.add(plate)
            main_window.session_recorder.rename_plate(name, plate_id)
            registry_id_by_config_name[name]= plate_id
            main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")

    main_window.ui.comboCType.clear()
    main_window.ui.comboCType.addItem(DEFAULT_CARBON_TYPE)
    main_window.atom_types= {DEFAULT_CARBON_TYPE: {"epsilon": 0.359824, "sigma": 3.39967}}
    for entry in cfg["atom_types"]:
        main_window.atom_types[entry["name"]]= {"epsilon": entry["epsilon"], "sigma": entry["sigma"]}
        main_window.ui.comboCType.addItem(entry["name"])
    main_window.update_ctype_controls_enabled()

    main_window.information_selected_atoms= []
    main_window.renderer.highlighted_atoms= []
    main_window.first_carbon= None
    main_window.set_oxide_mode(None)
    main_window.set_ctype_mode(None)

    if len(main_window.plates) > 0:
        main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)
        main_window.buttons_that_depend_of_having_a_plate(True)
    else:
        main_window.buttons_that_depend_of_having_a_plate(False)
    main_window.update_drawing_area()


def handle_undo(main_window):
    if main_window.session_recorder.undo():
        _rebuild_plates_from_recorder(main_window)


def handle_redo(main_window):
    if main_window.session_recorder.redo():
        _rebuild_plates_from_recorder(main_window)


def _resolve_atom_type_collision(main_window, name, incoming_params):
    existing= main_window.atom_types.get(name)
    if existing is None:
        return True
    if existing["epsilon"] == incoming_params["epsilon"] and existing["sigma"] == incoming_params["sigma"]:
        return False  # mismos valores -- no hay nada que resolver

    msg= QMessageBox(main_window)
    msg.setWindowTitle("Atom type collision")
    msg.setText(
        f"The current session already has a carbon type named {name!r} "
        f"(epsilon={existing['epsilon']}, sigma={existing['sigma']}), but the file "
        f"being added defines {name!r} with different values "
        f"(epsilon={incoming_params['epsilon']}, sigma={incoming_params['sigma']}).\n\n"
        "Overwriting affects every carbon using this type, in both the existing "
        "session and the file being added."
    )
    btn_keep= msg.addButton("Keep current session's", QMessageBox.ButtonRole.RejectRole)
    btn_overwrite= msg.addButton("Overwrite with file's", QMessageBox.ButtonRole.DestructiveRole)
    msg.exec()
    return msg.clickedButton() is btn_overwrite


def open_work(main_window):
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

    for name, parent_name, translation_raw, absolute, cnt_vector in core.iter_plate_build_order(cfg):
        plate= plates_by_name[name]

        if parent_name is not None:
            source_id= registry_id_by_config_name.get(parent_name)
            source_plate= plates_by_name[parent_name]
            dx, dy, dz= translation_raw
            translation= core.compute_duplicate_translation(dx, dy, dz, absolute, source_plate.get_geometric_center())
            plate_id= main_window.plates.add(plate, duplicate_of=source_id, translation=translation)

            if source_id is not None and main_window.session_recorder.has_plate(source_id):
                main_window.session_recorder.record_duplicate(
                    source_id, translation_raw, absolute, name=plate_id)
        else:
            plate_cfg= next(p for p in cfg["plates"] if p["name"] == name)
            plate_id= main_window.plates.add(plate)
            main_window.session_recorder.record_plate_created(plate_cfg.get("create", {}), name=plate_id)

        registry_id_by_config_name[name]= plate_id

        is_cnt= plate.get_is_CNT()
        if is_cnt:
            snapshot_carbons, snapshot_oxides, _unused_hydrogens= plate.backup_not_CNT
        else:
            snapshot_carbons, snapshot_oxides= plate.get_carbon_coords(), plate.get_oxide_coords()

        if main_window.session_recorder.has_plate(plate_id):
            if snapshot_oxides:
                oxide_atoms= [[x*10, y*10, z*10, t] for x, y, z, t, *_ in snapshot_oxides]
                main_window.session_recorder.record_oxidation_hard(plate_id, oxide_atoms)

            non_default_carbons= [c for c in snapshot_carbons if c[6] != DEFAULT_CARBON_TYPE]
            if non_default_carbons:
                by_type= {}
                for c in non_default_carbons:
                    by_type.setdefault(c[6], []).append(c)
                for ctype, carbons in by_type.items():
                    record_carbon_type_change(main_window, main_window.plates.position_of(plate_id), carbons, ctype)

            if is_cnt:
                main_window.session_recorder.record_cnt(plate_id, cnt_vector)

        main_window.ui.comboDrawings.addItem(f"Plate {len(main_window.plates)}")

    for name, params in atom_types.items():
        if not _resolve_atom_type_collision(main_window, name, params):
            continue
        is_new= name not in main_window.atom_types
        main_window.atom_types[name]= params
        if is_new:
            main_window.ui.comboCType.addItem(name)
        main_window.session_recorder.record_atom_type(name, params["epsilon"], params["sigma"])
    main_window.update_ctype_controls_enabled()

    if len(main_window.plates) > 0:
        main_window.ui.comboDrawings.setCurrentIndex(len(main_window.plates) - 1)
        main_window.buttons_that_depend_of_having_a_plate(True)
        main_window.update_drawing_area()

    print(f"{len(cfg['plates'])} plate(s) loaded from {file_name}")
