import gi
import os
import random
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import math
from logic.graphene import Graphene, generatePatterns
from logic.renderer import Renderer
from logic.export_formats import writeGRO, writeXYZ, writeTOP, writePDB
from logic.import_formats import readGRO, readXYZ, readPDB

class GrapheneApp:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/main.ui")
        self.builder.add_from_file("ui/dialog_prob.ui")
        self.builder.add_from_file("ui/dialog_create.ui")
        self.builder.add_from_file("ui/dialog_import.ui")
        self.builder.add_from_file("ui/dialog_export.ui")
        self.builder.add_from_file("ui/dialog_duplicate.ui")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("main_window")
        self.window.set_icon_from_file("ui/img/icon.png")

        self.drawing_area = self.builder.get_object("drawing_area")
        self.ruler_x = self.builder.get_object("ruler_x")
        self.ruler_y = self.builder.get_object("ruler_y")
        self.space_box_ruler_y = self.builder.get_object("space_box_ruler_y")
        self.btn_create = self.builder.get_object("btn_create")
        self.btn_duplicate = self.builder.get_object("btn_duplicate")
        self.btn_delete = self.builder.get_object("btn_delete")
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

        self.btn_reduce = self.builder.get_object("btn_reduce")

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

        self.dialog_duplicate = self.builder.get_object("dialog_duplicate")
        self.duplicate_label = self.builder.get_object("duplicate_label")
        self.radio_btn_relative_coords = self.builder.get_object("radio_btn_relative_coords")
        self.radio_btn_absolute_pos = self.builder.get_object("radio_btn_absolute_pos")
        self.spin_duplicate_x = self.builder.get_object("spin_duplicate_x")
        self.spin_duplicate_y = self.builder.get_object("spin_duplicate_y")
        self.spin_duplicate_z = self.builder.get_object("spin_duplicate_z")

        self.spin_prob_oh.connect("value-changed", self.on_spin_prob_oh_changed)
        self.spin_prob_o.connect("value-changed", self.on_spin_prob_o_changed)
        self.last_prob_oh = 66
        self.last_prob_o = 34

        self.buttons_that_depend_of_having_a_plate(False)

        self.plates = []
        self.plates_corresponding_to_duplicates = [[],[]]
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

        self.background_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "ui/img/background.svg", width=800, height=800, preserve_aspect_ratio=True
        )
        self.drawing_area.connect("draw", self.on_drawing_area_draw)


        self.window.connect("destroy", Gtk.main_quit)
        self.window.show_all()

    def buttons_that_depend_of_having_a_plate(self, active):
        self.btn_duplicate.set_sensitive(active)
        self.btn_delete.set_sensitive(active)
        self.btn_export.set_sensitive(active)
        self.btn_reduce.set_sensitive(active)
        self.btn_change_prob.set_sensitive(active)
        self.spin_random.set_sensitive(active)
        self.entry_selection.set_sensitive(active)
        self.btn_oh.set_sensitive(active)
        self.btn_o.set_sensitive(active)
        self.btn_remove_ox.set_sensitive(active)
        self.radio_random.set_sensitive(active)
        self.radio_z_plus.set_sensitive(active)
        self.radio_z_minus.set_sensitive(active)

    def on_main_window_destroy(self, window):
        print("Exiting...")
        print("Thanks for using Graphene-GUI")
        print("Please cite: No cite yet, stay in touch!")
        Gtk.main_quit()

    # # # # # # # # # # # # # # #
    # Main window: upper panel  #
    # # # # # # # # # # # # # # #
    def on_btn_create_clicked(self, button):
        self.dialog_create.show_all()
    
    def on_cb_plates_changed(self, combo):
        self.drawing_area.queue_draw()

    def on_btn_duplicate_clicked(self, button):
        self.dialog_duplicate.show_all()

    def on_btn_delete_clicked(self, button):
        index = self.cb_plates.get_active()
        if index < 0: return

        self.manage_duplicates_for_deletion(index+1, True)

        self.plates.pop(index)
        self.cb_plates.remove_all()
        for i in range(len(self.plates)):
            self.cb_plates.append_text(f"Plate {i + 1}")
        
        if self.plates:
            self.cb_plates.set_active(0)
        else:
            self.cb_plates.set_active(-1)
            self.buttons_that_depend_of_having_a_plate(False)
            self.spin_random.set_value(0)
            self.entry_selection.set_text("")

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
        self.manage_duplicates_for_deletion(self.cb_plates.get_active()+1, False)

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
    
    def on_drawing_area_draw(self, widget, cr):
        context = widget.get_style_context()
        Gtk.render_background(context, cr, 0, 0, widget.get_allocated_width(), widget.get_allocated_height())

        active_index = self.cb_plates.get_active()

        if active_index == -1 or not self.plates or not self.plates[active_index].get_number_atoms():
            allocation = widget.get_allocation()
            width, height = allocation.width, allocation.height

            scaled_pixbuf = self.background_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

            Gdk.cairo_set_source_pixbuf(cr, scaled_pixbuf, 0, 0)
            cr.paint()
            return False
        else:
            self.renderer.on_draw_drawing_area(widget, cr)
            return False



    # # # # # # # # # # # # # # #
    # Main window: lower panel  #
    # # # # # # # # # # # # # # #

    def on_btn_reduce_clicked(self, button):
        if self.cb_plates.get_active() == -1:
            return
        self.manage_duplicates_for_deletion(self.cb_plates.get_active()+1, False)

        plate = self.plates[self.cb_plates.get_active()]
        plate.remove_oxides()
        self.drawing_area.queue_draw()
        self.spin_random.set_value(0)
        self.entry_selection.set_text("")
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
        self.manage_duplicates_for_deletion(self.cb_plates.get_active()+1, False)

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
            plate.add_oxydation_to_list_of_carbon(oxide_new, self.z_mode, self.last_prob_oh)
            print(f"Finished with {len(oxide_new)} new oxides")

        except Exception as e:
            print("Not valid expression, exc=", e, end="\r")

        self.drawing_area.queue_draw()

    def set_oxide_mode(self, mode):
        self.active_oxide_mode = mode
        self.first_carbon = None

        self.btn_oh.set_active(mode == "OH")
        self.btn_o.set_active(mode == "O")
        self.btn_remove_ox.set_active(mode == "Remove")

    def on_btn_oh_clicked(self, button):
        if button.get_active():
            self.set_oxide_mode("OH")
        else:
            self.set_oxide_mode(None)

    def on_btn_o_clicked(self, button):
        if button.get_active():
            self.set_oxide_mode("O")
        else:
            self.set_oxide_mode(None)

    def on_btn_remove_ox_clicked(self, button):
        if button.get_active():
            self.set_oxide_mode("Remove")
        else:
            self.set_oxide_mode(None)

    def on_radio_toggled(self, button):
        if self.radio_z_plus.get_active():
            self.z_mode = 0
        elif self.radio_z_minus.get_active():
            self.z_mode = 1
        else:
            self.z_mode = 2


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

        plate = Graphene.create_from_params(n_x, n_y, center_x_nm, center_y_nm, center_z_nm, factor)
        self.plates.append(plate)

        self.cb_plates.append_text(f"Plate {len(self.plates)}")
        if len(self.plates) == 1:
            self.cb_plates.set_active(0)
        else:
            self.cb_plates.set_active(len(self.plates) - 1)

        self.drawing_area.queue_draw()
        self.buttons_that_depend_of_having_a_plate(True)

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
        filename = self.dialog_import.get_filename()
        if not filename:
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog_import,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="No file selected",
            )
            dialog.run()
            dialog.destroy()
            return

        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".gro":
                new_plates = readGRO(filename)
            elif ext == ".xyz":
                new_plates = readXYZ(filename)
            elif ext == ".pdb":
                new_plates = readPDB(filename)
            else:
                raise ValueError(f"Not supported file extension: {ext}")
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.dialog_import,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error reading file",
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()
            return

        for plate in new_plates:
            self.plates.append(plate)
            idx = len(self.plates)
            self.cb_plates.append_text(f"Plate {idx}")
            print(f"Importing coords: Plate {idx}")

        if new_plates:
            self.cb_plates.set_active(len(self.plates)-1)
            self.btn_export.set_sensitive(True)
            self.drawing_area.queue_draw()

        self.dialog_import.hide()
        print(f"{len(new_plates)} plate(s) imported from {filename}")

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
                text="No file selected",
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
                dialog = Gtk.MessageDialog(
                    transient_for=None,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.CANCEL,
                    text="Exporting topology..."
                )
                dialog.show_all()
                GLib.idle_add(lambda dialog, filename, plates, factor, duplicates: (writeTOP(filename, plates, factor, duplicates), dialog.destroy()))
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


    # # # # # # # # # # # # # # #
    #     Duplicate dialog      #
    # # # # # # # # # # # # # # #

    def on_btn_duplicate_ok_clicked(self, button):
        index_base = self.cb_plates.get_active()+1
        
        plate = self.plates[self.cb_plates.get_active()]
        translation = [self.spin_duplicate_x.get_value(), self.spin_duplicate_y.get_value(), self.spin_duplicate_z.get_value()]
        for i in range(3): translation[i] *= .1 # Change to nm
        if self.radio_btn_absolute_pos.get_active():
            plate_actual_center= plate.get_geometric_center()
            for i in range(3):
                translation[i] -= plate_actual_center[i]

        self.plates.append(plate.duplicate(translation))

        while(index_base in self.plates_corresponding_to_duplicates[0]):
            index_in_list= self.plates_corresponding_to_duplicates[0].index(index_base)
            index_base= self.plates_corresponding_to_duplicates[1][index_in_list]
        self.plates_corresponding_to_duplicates[0].append(len(self.plates))
        self.plates_corresponding_to_duplicates[1].append(index_base)

        self.cb_plates.append_text(f"Plate {len(self.plates)}")
        print(f"Duplicate added: Plate {len(self.plates)}")
        self.cb_plates.set_active(len(self.plates)-1)
        self.dialog_duplicate.hide()
    
    def on_btn_duplicate_cancel_clicked(self, button):
        self.dialog_duplicate.hide()

    def manage_duplicates_for_deletion(self, index, index_would_be_removed):
        # Controlled that it can not be at both list at the same time
        if index in self.plates_corresponding_to_duplicates[0]:
            # Stored as duplicate
            index_in_list= self.plates_corresponding_to_duplicates[0].index(index)
            self.plates_corresponding_to_duplicates[0].pop(index_in_list)
            self.plates_corresponding_to_duplicates[1].pop(index_in_list)
        elif index in self.plates_corresponding_to_duplicates[1]:
            # Stored as base
            indexes_in_list= []
            for i in range(len(self.plates_corresponding_to_duplicates[1])):
                if self.plates_corresponding_to_duplicates[1][i] == index:
                    indexes_in_list.append(i)

            if(len(indexes_in_list) == 1):
                self.plates_corresponding_to_duplicates[0].pop(indexes_in_list[0])
                self.plates_corresponding_to_duplicates[1].pop(indexes_in_list[0])
            else:
                new_base= self.plates_corresponding_to_duplicates[0][indexes_in_list[0]]
                for i in range(1, len(indexes_in_list)):
                    self.plates_corresponding_to_duplicates[1][indexes_in_list[i]] = new_base
                self.plates_corresponding_to_duplicates[0].pop(indexes_in_list[0])
                self.plates_corresponding_to_duplicates[1].pop(indexes_in_list[0])
        else:
            # Not stored
            return
        
        # Change numbers for deleting index
        if index_would_be_removed:
            for i in range(len(self.plates_corresponding_to_duplicates[0])):
                for j in range(2):
                    if self.plates_corresponding_to_duplicates[j][i] > index:
                        self.plates_corresponding_to_duplicates[j][i] -= 1

if __name__ == "__main__":
    app = GrapheneApp()
    Gtk.main()
    