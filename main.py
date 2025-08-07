import gi
import os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import math
from logic.graphene import Graphene, generatePatterns
from logic.renderer import Renderer
from logic.export_formats import writeGRO

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
        print(f"Plate {index} deleted")

    def on_btn_import_clicked(self, button):
        self.dialog_import.show_all()

    def on_btn_export_clicked(self, button):
        self.dialog_export.show_all()


    # # # # # # # # # # # # # # #
    # Main window: lower panel  #
    # # # # # # # # # # # # # # #

    def on_btn_reduce_clicked(self, button):
        plate = self.plates[self.cb_plates.get_active()]
        plate.remove_oxides()
        self.drawing_area.queue_draw()

    def on_btn_change_prob_clicked(self, button):
        self.last_prob_oh = self.spin_prob_oh.get_value()
        self.last_prob_o = self.spin_prob_o.get_value()
        self.dialog_prob.show_all()

    def on_spin_random_value_changed(self, spin):
        pass

    def on_entry_selection_changed(self, entry):
        expression = entry.get_text()
        self.spin_random.set_sensitive(not expression)
        if self.cb_plates.get_active() == -1:
            return
        plate = self.plates[self.cb_plates.get_active()]
        plate.remove_oxides()
        expression = entry.get_text()
        if not expression:
            return
        try:
            def evaluate_condition(x, y, z, expr):
                expr = expr.replace('and', ' and ').replace('or', ' or ').replace('not', ' not ')
                return eval(expr, {'x': x, 'y': y, 'z': z, 'and': lambda a, b: a and b, 'or': lambda a, b: a or b, 'not': lambda x: not x})

            list_carbons = []
            for coord in plate.get_carbon_coords():
                x, y, z = coord[:3]
                x, y, z = x * 10, y * 10, z * 10
                if evaluate_condition(x, y, z, expression):
                    list_carbons.append(coord)
            plate.add_oxydation_to_list_of_carbon(list_carbons, self.z_mode, self.last_prob_oh, self.last_prob_o)

            self.drawing_area.queue_draw()
            print(" "*60, end="\r")
        except Exception as e:
            print("Not valid expression, exc=", e, end="\r")

    def on_btn_oh_clicked(self, button):
        pass

    def on_btn_o_clicked(self, button):
        pass

    def on_btn_remove_ox_clicked(self, button):
        pass

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
            writeGRO(filename, self.plates)
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
    