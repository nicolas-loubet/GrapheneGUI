import gi
import os
import numpy as np
import random
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import math
from logic.graphene import Graphene, generatePatterns
from logic.renderer import Renderer
from logic.export_formats import writeGRO, writeXYZ, writeTOP, writePDB

class GrapheneApp:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/main.ui")
        self.builder.add_from_file("ui/dialog_prob.ui")
        self.builder.add_from_file("ui/dialog_create.ui")
        self.builder.add_from_file("ui/dialog_import.ui")
        self.builder.add_from_file("ui/dialog_export.ui")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("main_window")
        self.drawing_area = self.builder.get_object("drawing_area")
        self.ruler_x = self.builder.get_object("ruler_x")
        self.ruler_y = self.builder.get_object("ruler_y")
        self.space_box_ruler_y = self.builder.get_object("space_box_ruler_y")
        self.btn_create = self.builder.get_object("btn_create")
        self.btn_import = self.builder.get_object("btn_import")
        self.btn_export = self.builder.get_object("btn_export")
        self.cb_plates = self.builder.get_object("cb_plates")
        self.spin_random = self.builder.get_object("spin_random")
        self.entry_selection = self.builder.get_object("entry_selection")
        self.btn_oh = self.builder.get_object("btn_oh")
        self.btn_o = self.builder.get_object("btn_o")
        self.btn_remove_ox = self.builder.get_object("btn_remove_ox")
        self.btn_change_prob = self.builder.get_object("btn_change_prob")
        self.radio_random = self.builder.get_object("radio_random")
        self.radio_z_plus = self.builder.get_object("radio_z_plus")
        self.radio_z_minus = self.builder.get_object("radio_z_minus")
        self.entry_selection.connect("changed", self.on_entry_selection_changed)
        self.z_mode = 2
        self.radio_random.connect("toggled", self.on_radio_toggled)
        self.radio_z_plus.connect("toggled", self.on_radio_toggled)
        self.radio_z_minus.connect("toggled", self.on_radio_toggled)

        self.dialog_prob = self.builder.get_object("dialog_prob")
        self.spin_prob_oh = self.builder.get_object("spin_prob_oh")
        self.spin_prob_o = self.builder.get_object("spin_prob_o")
        self.btn_prob_ok = self.builder.get_object("btn_prob_ok")
        self.btn_prob_cancel = self.builder.get_object("btn_prob_cancel")
        self.dialog_create = self.builder.get_object("dialog_create")
        self.spin_width = self.builder.get_object("spin_width")
        self.spin_height = self.builder.get_object("spin_height")
        self.spin_center_x = self.builder.get_object("spin_center_x")
        self.spin_center_y = self.builder.get_object("spin_center_y")
        self.spin_center_z = self.builder.get_object("spin_center_z")
        self.btn_create_ok = self.builder.get_object("btn_create_ok")
        self.btn_create_cancel = self.builder.get_object("btn_create_cancel")
        self.spin_scale = self.builder.get_object("spin_scale")
        self.dialog_import = self.builder.get_object("dialog_import")
        self.btn_import_ok = self.builder.get_object("btn_import_ok")
        self.btn_import_cancel = self.builder.get_object("btn_import_cancel")
        self.dialog_export = self.builder.get_object("dialog_export")
        self.btn_export_ok = self.builder.get_object("btn_export_ok")
        self.btn_export_cancel = self.builder.get_object("btn_export_cancel")

        self.spin_prob_oh.connect("value-changed", self.on_spin_prob_oh_changed)
        self.spin_prob_o.connect("value-changed", self.on_spin_prob_o_changed)
        self.last_prob_oh = 66
        self.last_prob_o = 34

        self.plates = []
        self.renderer = Renderer(self.drawing_area, self.ruler_x, self.ruler_y, self.plates, self.cb_plates)

        self.drawing_area.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.connect("button-press-event", self.on_drawing_area_clicked)

        self.active_oxide_mode = None
        self.first_carbon = None

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("ui/styles.css")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.space_box_css_provider = Gtk.CssProvider()
        self.space_box_ruler_y.get_style_context().add_provider(
            self.space_box_css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.window.connect("destroy", Gtk.main_quit)
        self.window.show_all()


    # # # # # # # # # # # # # # #
    # Main window: upper panel  #
    # # # # # # # # # # # # # # #
    def on_btn_create_clicked(self, button):
        self.dialog_create.show_all()
    
    def on_cb_plates_changed(self, combo):
        self.drawing_area.queue_draw()

    def on_btn_delete_clicked(self, button):
        index = self.cb_plates.get_active()
        if index < 0: return

        self.plates.pop(index)
        self.cb_plates.remove_all()
        for i in range(len(self.plates)):
            self.cb_plates.append_text(f"Plate {i + 1}")
        
        if self.plates:
            self.cb_plates.set_active(0)
        else:
            self.cb_plates.set_active(-1)
        
        self.drawing_area.queue_draw()
        print(f"Plate {index+1} deleted")

    def on_btn_import_clicked(self, button):
        self.dialog_import.show_all()

    def on_btn_export_clicked(self, button):
        self.dialog_export.show_all()


    # # # # # # # # # # # # # # #
    # Main window: middle panel #
    # # # # # # # # # # # # # # #

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
            self.drawing_area.queue_draw()
            print(f"Added O at ({o_x*10:.2f}, {o_y*10:.2f}, {o_z*10:.2f}) and H at ({o_x:.3f}, {o_y:.3f}, {h_z:.3f})")
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
                self.drawing_area.queue_draw()
                print(f"Added O at ({o_x*10:.2f}, {o_y*10:.2f}, {o_z*10:.2f})")
            else:
                print("Position already occupied by an oxide")
        else:
            print("Second carbon is not adjacent to the first")
        self.first_carbon = None

    def on_drawing_area_clicked(self, widget, event):
        if self.cb_plates.get_active() == -1 or not self.active_oxide_mode:
            return False

        plate = self.plates[self.cb_plates.get_active()]
        x, y = event.x, event.y
        x_nm, y_nm = self.renderer.pixel_to_nm(x, y)

        carbon = plate.get_nearest_carbon(x_nm, y_nm)
        if not carbon:
            return False

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
            list_remove_ox= plate.get_oxides_for_carbon(carbon)
            for ox in list_remove_ox:
                plate.remove_atom_oxide(ox)
            self.drawing_area.queue_draw()
            plate.recheck_ox_indexes()
            print(f"{len(list_remove_ox)} atom{("s" if len(list_remove_ox) != 1 else "")} removed")

        return True


    # # # # # # # # # # # # # # #
    # Main window: lower panel  #
    # # # # # # # # # # # # # # #

    def on_btn_reduce_clicked(self, button):
        if self.cb_plates.get_active() == -1:
            return
        plate = self.plates[self.cb_plates.get_active()]
        plate.remove_oxides()
        self.drawing_area.queue_draw()
        print("Oxides removed")

    def on_btn_change_prob_clicked(self, button):
        self.last_prob_oh = self.spin_prob_oh.get_value()
        self.last_prob_o = self.spin_prob_o.get_value()
        self.dialog_prob.show_all()

    def on_spin_random_value_changed(self, spin):
        self.put_oxides(self.entry_selection.get_text())

    def on_entry_selection_changed(self, entry):
        self.put_oxides(entry.get_text())

    def put_oxides(self, expr):
        if self.cb_plates.get_active() == -1:
            return
        fraction_oxidation= self.spin_random.get_value()/100
        plate= self.plates[self.cb_plates.get_active()]
        plate.remove_oxides()
        
        if not expr: expr= ""

        def evaluate_condition(x, y, z, i_atom, expr):
            if expr == "": return True
            expr = expr.replace('and', ' and ').replace('or', ' or ').replace('not', ' not ')
            return eval(expr, {'x': x, 'y': y, 'z': z, 'index': i_atom, 'and': lambda a, b: a and b, 'or': lambda a, b: a or b, 'not': lambda x: not x})

        try:
            list_carbons_in_expression = []
            for coord in plate.get_carbon_coords():
                x, y, z, _, i_atom = coord
                x, y, z = x * 10, y * 10, z * 10
                if evaluate_condition(x, y, z, i_atom, expr):
                    list_carbons_in_expression.append(coord)
            
            number_oxidations_desired= int(len(list_carbons_in_expression)*fraction_oxidation)
            
            oxide_new= random.sample(list_carbons_in_expression, min(number_oxidations_desired, len(list_carbons_in_expression)))
            plate.add_oxydation_to_list_of_carbon(oxide_new, self.z_mode, self.last_prob_oh, self.last_prob_o)
            print(f"Finished with {len(oxide_new)} new oxides"+" "*40, end="\r")

        except Exception as e:
            print("Not valid expression, exc=", e, end="\r")

        self.drawing_area.queue_draw()

    def on_btn_oh_clicked(self, button):
        self.active_oxide_mode = "OH" if self.active_oxide_mode != "OH" else None
        self.first_carbon = None
        print(f"OH mode {'activated' if self.active_oxide_mode == 'OH' else 'deactivated'}")

    def on_btn_o_clicked(self, button):
        self.active_oxide_mode = "O" if self.active_oxide_mode != "O" else None
        self.first_carbon = None
        print(f"O mode {'activated' if self.active_oxide_mode == 'O' else 'deactivated'}")

    def on_btn_remove_ox_clicked(self, button):
        self.active_oxide_mode = "Remove" if self.active_oxide_mode != "Remove" else None
        self.first_carbon = None
        print(f"Remove mode {'activated' if self.active_oxide_mode == 'Remove' else 'deactivated'}")

    def on_radio_toggled(self, button):
        if self.radio_z_plus.get_active():
            self.z_mode = 0  # z+
        elif self.radio_z_minus.get_active():
            self.z_mode = 1  # z-
        else:
            self.z_mode = 2  # z±


    # # # # # # # # # # # # # # #
    #       Create dialog       #
    # # # # # # # # # # # # # # #

    def on_btn_create_ok_clicked(self, button):
        width = self.spin_width.get_value()
        height = self.spin_height.get_value()
        center_x = self.spin_center_x.get_value()
        center_y = self.spin_center_y.get_value()
        center_z = self.spin_center_z.get_value()
        factor = self.spin_scale.get_value()/100.0

        width_nm = width / 10
        height_nm = height / 10
        center_x_nm = center_x / 10
        center_y_nm = center_y / 10
        center_z_nm = center_z / 10

        n_x = math.floor(width_nm / (2 * 0.1225 * factor))
        n_y = math.floor(height_nm / (6 * 0.071 * factor))

        max_atoms = len(generatePatterns())
        max_n_x_n_y = max_atoms // (2 * (2 * n_x + 1)) if n_x > 0 else 0
        if n_y > max_n_x_n_y:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Too large",
            )
            dialog.format_secondary_text(
                f"The number of atoms is too large ({max_atoms}). Reduce the width or height."
            )
            dialog.run()
            dialog.destroy()
            return

        plate = Graphene(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor)
        self.plates.append(plate)

        self.cb_plates.append_text(f"Plate {len(self.plates)}")
        if len(self.plates) == 1:
            self.cb_plates.set_active(0)
        else:
            self.cb_plates.set_active(len(self.plates) - 1)

        self.drawing_area.queue_draw()

        css = b"""
        #space_box_ruler_y {
            background-color: white;
        }
        """
        self.space_box_css_provider.load_from_data(css)

        self.dialog_create.hide()
        print(f"Coords drawn: Plate {len(self.plates)}")

    def on_btn_create_cancel_clicked(self, button):
        self.dialog_create.hide()


    # # # # # # # # # # # # # # #
    #       Import dialog       #
    # # # # # # # # # # # # # # #
    
    def on_btn_import_ok_clicked(self, button):
        self.dialog_import.hide()

    def on_btn_import_cancel_clicked(self, button):
        self.dialog_import.hide()


    # # # # # # # # # # # # # # #
    #       Export dialog       #
    # # # # # # # # # # # # # # #
    
    def on_btn_export_ok_clicked(self, button):
        filename = self.dialog_export.get_filename()
        if filename == None or len(filename) == 0:
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog_export,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="No filename",
            )
            dialog.run()
            dialog.destroy()
            return
        if filename.find(".") == -1:
            filename += ".gro"
        if filename and self.plates:
            if os.path.exists(filename):
                dialog = Gtk.MessageDialog(
                    transient_for=self.dialog_export,
                    flags=0,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="File exists",
                )
                dialog.format_secondary_text(f"Do you want to overwrite {filename}?")
                response = dialog.run()
                dialog.destroy()
                if response != Gtk.ResponseType.YES:
                    return
                
            if filename.endswith(".gro"):
                writeGRO(filename, self.plates)
            elif filename.endswith(".pdb"):
                writePDB(filename, self.plates)
            elif filename.endswith(".xyz"):
                writeXYZ(filename, self.plates)
            elif filename.endswith(".top"):
                factor = self.spin_scale.get_value()/100.0
                writeTOP(filename, self.plates, factor)
            else:
                dialog = Gtk.MessageDialog(
                    transient_for=self.dialog_export,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Unsupported format",
                )
                dialog.format_secondary_text(f"Unsupported format: {filename}")
                dialog.run()
                dialog.destroy()
                return
        self.dialog_export.hide()

    def on_btn_export_cancel_clicked(self, button):
        self.dialog_export.hide()


    # # # # # # # # # # # # # # #
    #    Probability dialog     #
    # # # # # # # # # # # # # # #
    
    def on_spin_prob_oh_changed(self, spin):
        value = spin.get_value()
        self.spin_prob_o.set_value(100 - value)

    def on_spin_prob_o_changed(self, spin):
        value = spin.get_value()
        self.spin_prob_oh.set_value(100 - value)

    def on_btn_prob_ok_clicked(self, button):
        self.last_prob_oh = self.spin_prob_oh.get_value()
        self.last_prob_o = self.spin_prob_o.get_value()
        self.dialog_prob.hide()

    def on_btn_prob_cancel_clicked(self, button):
        self.spin_prob_oh.set_value(self.last_prob_oh)
        self.spin_prob_o.set_value(self.last_prob_o)
        self.dialog_prob.hide()


if __name__ == "__main__":
    app = GrapheneApp()
    Gtk.main()
    