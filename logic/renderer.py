import math
import numpy as np
from gi.repository import Gtk, Gdk, GLib

class Renderer:
    limits: list  # xy values of minimum and maximum values drawn

    def __init__(self, drawing_area, ruler_x, ruler_y, plates, cb_plates):
        self.drawing_area = drawing_area
        self.ruler_x = ruler_x
        self.ruler_y = ruler_y
        self.plates = plates
        self.cb_plates = cb_plates
        self.scale = 1.0
        self.center_x = 0.0
        self.center_y = 0.0
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.limits = [0.0, 0.0, 0.0, 0.0]

        self.drawing_area.connect("draw", self.on_draw_drawing_area)
        self.ruler_x.connect("draw", self.on_draw_ruler_x)
        self.ruler_y.connect("draw", self.on_draw_ruler_y)

        self.drawing_area.set_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect("motion-notify-event", self.on_motion_notify)

    def on_motion_notify(self, widget, event):
        if not self.plates or self.cb_plates.get_active() == -1:
            widget.set_tooltip_text("")
            return
        plate = self.plates[self.cb_plates.get_active()]
        x_win, y_win = event.x, event.y
        x = x_win / self.scale + self.center_x - widget.get_allocated_width() / (2 * self.scale)
        y = y_win / self.scale + self.center_y - widget.get_allocated_height() / (2 * self.scale)
        for coord in plate.get_carbon_coords():
            x_atom, y_atom, z_atom, name, _ = coord
            if (x - x_atom)**2 + (y - y_atom)**2 < 0.01:
                widget.set_tooltip_text(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                return
        for coord in plate.get_oxide_coords():
            x_atom, y_atom, z_atom, name, _ = coord
            if (x - x_atom)**2 + (y - y_atom)**2 < 0.01:
                widget.set_tooltip_text(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                return
        widget.set_tooltip_text("")

    def update_plate_metrics(self, widget):
        if not self.plates or self.cb_plates.get_active() == -1:
            self.scale = 1.0
            self.min_x = self.max_x = self.min_y = self.max_y = 0.0
            self.center_x = self.center_y = 0.0
            self.limits = [0.0, 0.0, 0.0, 0.0]
            return

        plate_index = self.cb_plates.get_active()
        plate = self.plates[plate_index]

        width = self.drawing_area.get_allocated_width()
        height = self.drawing_area.get_allocated_height()

        carbon_coords = plate.get_carbon_coords()
        if not carbon_coords:
            self.scale = 1.0
            self.min_x = self.max_x = self.min_y = self.max_y = 0.0
            self.center_x = self.center_y = 0.0
            self.limits = [0.0, 0.0, 0.0, 0.0]
            return

        x_coords = [coord[0] for coord in carbon_coords]
        y_coords = [coord[1] for coord in carbon_coords]
        self.min_x, self.max_x = min(x_coords), max(x_coords)
        self.min_y, self.max_y = min(y_coords), max(y_coords)
        plate_width = self.max_x - self.min_x
        plate_height = self.max_y - self.min_y

        self.limits = [self.min_x, self.max_x, self.min_y, self.max_y]

        self.scale = min(width / (plate_width * 1.1), height / (plate_height * 1.1))
        self.center_x = (self.min_x + self.max_x) / 2
        self.center_y = (self.min_y + self.max_y) / 2

    def on_draw_drawing_area(self, widget, cr):
        self.update_plate_metrics(widget)
        if not self.plates or self.cb_plates.get_active() == -1:
            return

        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        cr.save()
        cr.scale(self.scale, self.scale)
        cr.translate(width / (2 * self.scale) - self.center_x, height / (2 * self.scale) - self.center_y)

        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        plate_index = self.cb_plates.get_active()
        plate = self.plates[plate_index]

        cr.set_source_rgb(0, 0, 0)
        for coord in plate.get_carbon_coords():
            x = coord[0]
            y = coord[1]
            cr.arc(x, y, 0.03, 0, 2 * math.pi)
            cr.fill()

        for x, y, _, oxide_type, _ in plate.get_oxide_coords():
            if oxide_type == "OO":
                cr.set_source_rgb(1, 0, 0)
            elif oxide_type == "OE":
                cr.set_source_rgb(0, 0, 1)
            elif oxide_type == "HO":
                cr.set_source_rgb(.8, .8, .8)
            cr.arc(x, y, 0.015, 0, 2 * math.pi)
            cr.fill()

        cr.restore()

        GLib.idle_add(self.redraw_rulers)

    def redraw_rulers(self):
        self.ruler_x.queue_draw()
        self.ruler_y.queue_draw()
        return False

    def on_draw_ruler_x(self, widget, cr):
        if not self.plates or self.cb_plates.get_active() == -1:
            return

        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        pixel_x_min = (self.min_x - self.center_x) * self.scale + width / 2
        pixel_x_max = (self.max_x - self.center_x) * self.scale + width / 2

        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(2.0)
        cr.move_to(pixel_x_min, height / 2)
        cr.line_to(pixel_x_max, height / 2)
        cr.stroke()

        cr.set_font_size(12)
        for x in range(int(self.limits[0]*10), int(self.limits[1]*10) + 1):
            pixel_x = (x/10 - self.center_x) * self.scale + width / 2
            cr.move_to(pixel_x, height / 2)
            cr.line_to(pixel_x, height / 2 - (10 if x % 10 == 0 else 8 if x % 5 == 0 else 5))
            cr.stroke()

    def on_draw_ruler_y(self, widget, cr):
        if not self.plates or self.cb_plates.get_active() == -1:
            return

        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        pixel_y_min = (self.min_y - self.center_y) * self.scale + height / 2
        pixel_y_max = (self.max_y - self.center_y) * self.scale + height / 2

        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(2.0)
        cr.move_to(width / 2, pixel_y_min)
        cr.line_to(width / 2, pixel_y_max)
        cr.stroke()

        cr.set_font_size(12)
        for y in range(int(self.limits[2]*10), int(self.limits[3]*10) + 1):
            pixel_y = (y/10 - self.center_y) * self.scale + height / 2
            cr.move_to(width / 2, pixel_y)
            cr.line_to(width / 2 - (10 if y % 10 == 0 else 8 if y % 5 == 0 else 5), pixel_y)
            cr.stroke()
            