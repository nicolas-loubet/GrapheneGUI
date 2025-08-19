from PySide6.QtGui import QPainter, QColor, QPen, QFont, QImage
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPixmap
from .export_formats import checkBounds
import importlib.resources as pkg_resources
import numpy as np
import warnings

class Renderer:
    def __init__(self, drawing_area, ruler_x, ruler_y, plates, cb_plates, is_dark_mode_func):
        self.drawing_area = drawing_area
        self.ruler_x = ruler_x
        self.ruler_y = ruler_y
        self.plates = plates
        self.cb_plates = cb_plates
        self.is_dark_mode_func = is_dark_mode_func

        self.scale = 1.0
        self.center_x = 0.0
        self.center_y = 0.0
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.limits = [0.0, 0.0, 0.0, 0.0]

        self.roll_vector= None

        self.drawing_area.setMouseTracking(True)
        self.drawing_area.mouseMoveEvent = self.on_motion_notify
        self.ruler_x.paintEvent = self.on_draw_ruler_x
        self.ruler_y.paintEvent = self.on_draw_ruler_y
        self.drawing_area.paintEvent = self.on_draw_drawing_area

        self.colors = {
            "dark": {
                "bg": QColor("#3d3d3d"),
                "carbon": QColor("#00ffff"),
                "oxide_OO": QColor("#e71616"),
                "oxide_OE": QColor("#e4bd19"),
                "oxide_HO": QColor("#c8c8c8")
            },
            "light": {
                "bg": QColor("#ffffff"),
                "carbon": QColor("#000000"),
                "oxide_OO": QColor("#ff0000"),
                "oxide_OE": QColor("#0000ff"),
                "oxide_HO": QColor("#969696")
            }
        }

        self.update_view()

    def update_view(self):
        self.drawing_area.viewport().update()
        self.ruler_x.update()
        self.ruler_y.update()

    def _event_pos_to_point(self, event):
        p = event.position() if hasattr(event, "position") else event.pos()
        return float(p.x()), float(p.y())

    def pixel_to_nm(self, x_win, y_win):
        if not self.plates or self.cb_plates.currentIndex() == -1 or self.scale == 0: return None, None

        width = float(self.drawing_area.width())
        height = float(self.drawing_area.height())
        x_nm = x_win / self.scale + self.center_x - width / (2.0 * self.scale)
        y_nm = y_win / self.scale + self.center_y - height / (2.0 * self.scale)
        return x_nm, y_nm

    def on_motion_notify(self, event):
        if not self.plates or self.cb_plates.currentIndex() == -1:
            self.drawing_area.setToolTip("")
            return
        x_px, y_px = self._event_pos_to_point(event)
        x_nm, y_nm = self.pixel_to_nm(x_px, y_px)
        if x_nm is None:
            self.drawing_area.setToolTip("")
            return
        plate = self.plates[self.cb_plates.currentIndex()]
        for coords in (plate.get_carbon_coords(), plate.get_oxide_coords()):
            for x_atom, y_atom, z_atom, name, _ in coords:
                if (x_nm - x_atom) ** 2 + (y_nm - y_atom) ** 2 < 0.01:
                    self.drawing_area.setToolTip(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                    return
        self.drawing_area.setToolTip("")

    def update_plate_metrics(self):
        if not self.plates or self.cb_plates.currentIndex() == -1:
            self.scale = 1.0
            self.min_x = self.max_x = self.min_y = self.max_y = self.center_x = self.center_y = 0.0
            self.limits = [0.0, 0.0, 0.0, 0.0]
            return
        plate = self.plates[self.cb_plates.currentIndex()]
        width = max(1.0, float(self.drawing_area.width()))
        height = max(1.0, float(self.drawing_area.height()))
        carbon_coords = plate.get_carbon_coords()
        if not carbon_coords:
            self.scale = 1.0
            self.min_x = self.max_x = self.min_y = self.max_y = self.center_x = self.center_y = 0.0
            self.limits = [0.0, 0.0, 0.0, 0.0]
            return
        x_coords, y_coords = zip(*[(c[0], c[1]) for c in carbon_coords])
        self.min_x, self.max_x = min(x_coords), max(x_coords)
        self.min_y, self.max_y = min(y_coords), max(y_coords)
        plate_width = max(1e-6, self.max_x - self.min_x)
        plate_height = max(1e-6, self.max_y - self.min_y)
        self.limits = [self.min_x, self.max_x, self.min_y, self.max_y]
        self.scale = max(1.0, min(width / (plate_width * 1.1), height / (plate_height * 1.1)))
        self.center_x = (self.min_x + self.max_x) / 2.0
        self.center_y = (self.min_y + self.max_y) / 2.0

    def _draw_plate(self, painter, plate, is_dark_mode):
        mode= "dark" if is_dark_mode else "light"
        colors= self.colors[mode]

        painter.fillRect(QRectF(-1000, -1000, 2000, 2000), colors["bg"])
        painter.setPen(Qt.NoPen)

        carbons,oxides= plate.get_carbon_coords(),plate.get_oxide_coords()

        if not plate.get_is_CNT():
            # Case 1: Flat graphene (original behavior)
            painter.setBrush(colors["carbon"])
            for x, y, *_ in carbons:
                painter.drawEllipse(QPointF(x, y), 0.035, 0.035)

            for x, y, _, oxide_type, _ in oxides:
                painter.setBrush(colors[f"oxide_{oxide_type}"])
                painter.drawEllipse(QPointF(x, y), 0.035, 0.035)
        else:
            # Case 2: CNT (rolled)
            x_ref, y_ref= carbons[0][0], carbons[0][1]
            # Asume centrado en 00, adaptar
            R= np.sqrt((x_ref**2 + y_ref**2))
            mins,bounds= checkBounds([plate])

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=Warning)
                a_zr, b_zr, c_zr= np.polyfit([mins[2], bounds[2]+mins[2]], [R*0.1, R], 2)

            a_zs,b_zs= np.polyfit([mins[2],bounds[2]+mins[2]],[.1,1],1)
            painter.setBrush(colors["carbon"])
            for x, y, z, *_ in carbons:
                angle= np.arctan(y/x)
                if x<0: angle+= np.pi
                r_new= a_zr*z*z+b_zr*z+c_zr
                xn,yn= r_new*np.cos(angle), r_new*np.sin(angle)
                scale= a_zs*z+b_zs
                painter.drawEllipse(QPointF(xn, yn), 0.035*scale, 0.035*scale)

            for x, y, _, oxide_type, _ in oxides:
                painter.setBrush(colors[f"oxide_{oxide_type}"])
                painter.drawEllipse(QPointF(x, y), 0.035, 0.035)

    def set_roll_vector(self, roll_vector):
        self.roll_vector= roll_vector

    def on_draw_drawing_area(self, event):
        painter = QPainter(self.drawing_area.viewport())
        mode = "dark" if self.is_dark_mode_func() else "light"
        bg_color = self.colors[mode]["bg"]
        try:
            if not self.plates or self.cb_plates.currentIndex() == -1:
                pixmap = QPixmap(str(pkg_resources.files("graphenegui.ui.img").joinpath("background.svg")))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.drawing_area.viewport().size(),
                                                Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation)
                    point = QPointF(
                        (self.drawing_area.viewport().width() - scaled_pixmap.width()) / 2,
                        (self.drawing_area.viewport().height() - scaled_pixmap.height()) / 2
                    )
                    painter.drawPixmap(point, scaled_pixmap)
                else:
                    painter.fillRect(self.drawing_area.viewport().rect(), bg_color)
                return

            painter.setRenderHint(QPainter.Antialiasing)
            self.update_plate_metrics()
            if not self.plates or self.cb_plates.currentIndex() == -1:
                painter.fillRect(self.drawing_area.viewport().rect(), bg_color)
                return
            width, height = float(self.drawing_area.viewport().width()), float(self.drawing_area.viewport().height())
            painter.save()
            painter.scale(self.scale, self.scale)
            painter.translate(width / (2.0 * self.scale) - self.center_x, height / (2.0 * self.scale) - self.center_y)
            self._draw_plate(painter, self.plates[self.cb_plates.currentIndex()], self.is_dark_mode_func())
            painter.restore()
            self.ruler_x.update()
            self.ruler_y.update()
        finally:
            if painter.isActive():
                painter.end()

    def on_draw_ruler_x(self, event):
        painter = QPainter(self.ruler_x)
        try:
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.fillRect(self.ruler_x.rect(), self.colors["dark" if self.is_dark_mode_func() else "light"]["bg"])
            if not self.plates or self.cb_plates.currentIndex() == -1: return

            width, height = float(self.ruler_x.width()), float(self.ruler_x.height())
            pixel_x_min = (self.min_x - self.center_x) * self.scale + width / 2.0
            pixel_x_max = (self.max_x - self.center_x) * self.scale + width / 2.0
            pen = QPen()
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(pixel_x_min, 3.7 * height / 4.0, pixel_x_max, 3.7 * height / 4.0)
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            for x in range(int(self.limits[0] * 10), int(self.limits[1] * 10) + 1):
                pixel_x = (x / 10.0 - self.center_x) * self.scale + width / 2.0
                tick_height = 10 if x % 10 == 0 else 8 if x % 5 == 0 else 5
                if x % 10 == 0:
                    painter.drawText(int(pixel_x - 15), int(0.6*height/4), 30, 20, Qt.AlignCenter, str(x))
                painter.drawLine(pixel_x, 3.7 * height / 4.0, pixel_x, 3.7 * height / 4.0 - tick_height)
        finally:
            if painter.isActive():
                painter.end()

    def on_draw_ruler_y(self, event):
        painter = QPainter(self.ruler_y)
        try:
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.fillRect(self.ruler_y.rect(), self.colors["dark" if self.is_dark_mode_func() else "light"]["bg"])
            if not self.plates or self.cb_plates.currentIndex() == -1: return

            width, height = float(self.ruler_y.width()), float(self.ruler_y.height())
            pixel_y_min = (self.min_y - self.center_y) * self.scale + height / 2.0
            pixel_y_max = (self.max_y - self.center_y) * self.scale + height / 2.0
            pen = QPen()
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(3.7 * width / 4.0, pixel_y_min, 3.7 * width / 4.0, pixel_y_max)
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            for y in range(int(self.limits[2] * 10), int(self.limits[3] * 10) + 1):
                pixel_y = (y / 10.0 - self.center_y) * self.scale + height / 2.0
                tick_width = 10 if y % 10 == 0 else 8 if y % 5 == 0 else 5
                if y % 10 == 0:
                    painter.drawText(int(0.1*width/4), int(pixel_y - 10), 30, 20, Qt.AlignCenter, str(y))
                painter.drawLine(3.7 * width / 4.0, pixel_y, 3.7 * width / 4.0 - tick_width, pixel_y)
        finally:
            if painter.isActive():
                painter.end()

    def render_plate(self, plate, is_dark_mode):
        width, height = max(1, int(self.drawing_area.width())), max(1, int(self.drawing_area.height()))
        image = QImage(width, height, QImage.Format_RGB32)
        mode = "dark" if is_dark_mode else "light"
        image.fill(self.colors[mode]["bg"])
        temp_painter = QPainter(image)
        try:
            temp_painter.setRenderHint(QPainter.Antialiasing)
            self.update_plate_metrics()
            temp_painter.save()
            temp_painter.scale(self.scale, self.scale)
            temp_painter.translate(width / (2.0 * self.scale) - self.center_x, height / (2.0 * self.scale) - self.center_y)
            self._draw_plate(temp_painter, plate, is_dark_mode)
            temp_painter.restore()
        finally:
            if temp_painter.isActive():
                temp_painter.end()
        return image
