import math
import numpy as np
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QImage, QPixmap
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import QWidget, QGraphicsScene

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

        # Conectar eventos
        self.drawing_area.paintEvent = self.on_draw_drawing_area
        self.ruler_x.paintEvent = self.on_draw_ruler_x
        self.ruler_y.paintEvent = self.on_draw_ruler_y
        
        # Habilitar seguimiento de ratón
        self.drawing_area.setMouseTracking(True)
        self.drawing_area.mouseMoveEvent = self.on_motion_notify

    def pixel_to_nm(self, x_win, y_win):
        if not self.plates or self.cb_plates.currentIndex() == -1:
            return None, None

        width = self.drawing_area.width()
        height = self.drawing_area.height()

        x_nm = x_win / self.scale + self.center_x - width / (2 * self.scale)
        y_nm = y_win / self.scale + self.center_y - height / (2 * self.scale)
        return x_nm, y_nm

    def on_motion_notify(self, event):
        if not self.plates or self.cb_plates.currentIndex() == -1:
            self.drawing_area.setToolTip("")
            return

        plate = self.plates[self.cb_plates.currentIndex()]
        x_nm, y_nm = self.pixel_to_nm(event.position().x(), event.position().y())
        if x_nm is None:
            self.drawing_area.setToolTip("")
            return

        for coord in plate.get_carbon_coords():
            x_atom, y_atom, z_atom, name, _ = coord
            if (x_nm - x_atom)**2 + (y_nm - y_atom)**2 < 0.01:
                self.drawing_area.setToolTip(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                return
        for coord in plate.get_oxide_coords():
            x_atom, y_atom, z_atom, name, _ = coord
            if (x_nm - x_atom)**2 + (y_nm - y_atom)**2 < 0.01:
                self.drawing_area.setToolTip(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                return
        self.drawing_area.setToolTip("")

    def update_plate_metrics(self):
        if not self.plates or self.cb_plates.currentIndex() == -1:
            self.scale = 1.0
            self.min_x = self.max_x = self.min_y = self.max_y = 0.0
            self.center_x = self.center_y = 0.0
            self.limits = [0.0, 0.0, 0.0, 0.0]
            return

        plate_index = self.cb_plates.currentIndex()
        plate = self.plates[plate_index]

        width = self.drawing_area.width()
        height = self.drawing_area.height()

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

    def on_draw_drawing_area(self, event):
        painter = QPainter(self.drawing_area)
        self.update_plate_metrics()
        
        if not self.plates or self.cb_plates.currentIndex() == -1:
            # Dibujar fondo
            if self.is_dark_mode_func():
                painter.fillRect(self.drawing_area.rect(), QColor(30, 30, 30))
            else:
                painter.fillRect(self.drawing_area.rect(), Qt.white)
            return

        width = self.drawing_area.width()
        height = self.drawing_area.height()

        # Guardar estado del painter
        painter.save()
        painter.scale(self.scale, self.scale)
        painter.translate(width / (2 * self.scale) - self.center_x, 
                         height / (2 * self.scale) - self.center_y)

        # Dibujar fondo
        if self.is_dark_mode_func():
            painter.fillRect(QRectF(-1000, -1000, 2000, 2000), QColor(30, 30, 30))
        else:
            painter.fillRect(QRectF(-1000, -1000, 2000, 2000), Qt.white)

        plate_index = self.cb_plates.currentIndex()
        plate = self.plates[plate_index]

        # Dibujar átomos de carbono
        if self.is_dark_mode_func():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 255, 255))  # Cian para modo oscuro
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.black)
            
        for coord in plate.get_carbon_coords():
            x = coord[0]
            y = coord[1]
            painter.drawEllipse(QPointF(x, y), 0.035, 0.035)

        # Dibujar óxidos
        for coord in plate.get_oxide_coords():
            x, y, _, oxide_type, _ = coord
            if oxide_type == "OO":
                painter.setBrush(QColor(255, 0, 0))  # Rojo
            elif oxide_type == "OE":
                painter.setBrush(QColor(0, 0, 255))  # Azul
            elif oxide_type == "HO":
                if self.is_dark_mode_func():
                    painter.setBrush(QColor(200, 200, 200))  # Gris claro
                else:
                    painter.setBrush(QColor(150, 150, 150))  # Gris
                    
            painter.drawEllipse(QPointF(x, y), 0.025, 0.025)

        # Restaurar estado del painter
        painter.restore()
        
        # Actualizar reglas
        self.ruler_x.update()
        self.ruler_y.update()

    def on_draw_ruler_x(self, event):
        painter = QPainter(self.ruler_x)
        if not self.plates or self.cb_plates.currentIndex() == -1:
            if self.is_dark_mode_func():
                painter.fillRect(self.ruler_x.rect(), QColor(30, 30, 30))
            else:
                painter.fillRect(self.ruler_x.rect(), Qt.white)
            return

        width = self.ruler_x.width()
        height = self.ruler_x.height()

        if self.is_dark_mode_func():
            painter.fillRect(self.ruler_x.rect(), QColor(30, 30, 30))
            painter.setPen(Qt.white)
        else:
            painter.fillRect(self.ruler_x.rect(), Qt.white)
            painter.setPen(Qt.black)
            
        pixel_x_min = (self.min_x - self.center_x) * self.scale + width / 2
        pixel_x_max = (self.max_x - self.center_x) * self.scale + width / 2

        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(pixel_x_min, 3*height / 4, pixel_x_max, 3*height / 4)

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        for x in range(int(self.limits[0]*10), int(self.limits[1]*10) + 1):
            pixel_x = (x/10 - self.center_x) * self.scale + width / 2
            
            if x % 10 == 0:
                tick_height = 10
                # Dibujar etiqueta
                painter.drawText(int(pixel_x-15), int(height / 2), 30, 20, 
                                Qt.AlignCenter, str(x))
            elif x % 5 == 0:
                tick_height = 8
            else:
                tick_height = 5
                
            painter.drawLine(pixel_x, 3*height / 4, 
                            pixel_x, 3*height / 4 - tick_height)

    def on_draw_ruler_y(self, event):
        painter = QPainter(self.ruler_y)
        if not self.plates or self.cb_plates.currentIndex() == -1:
            if self.is_dark_mode_func():
                painter.fillRect(self.ruler_y.rect(), QColor(30, 30, 30))
            else:
                painter.fillRect(self.ruler_y.rect(), Qt.white)
            return

        width = self.ruler_y.width()
        height = self.ruler_y.height()

        if self.is_dark_mode_func():
            painter.fillRect(self.ruler_y.rect(), QColor(30, 30, 30))
            painter.setPen(Qt.white)
        else:
            painter.fillRect(self.ruler_y.rect(), Qt.white)
            painter.setPen(Qt.black)
            
        pixel_y_min = (self.min_y - self.center_y) * self.scale + height / 2
        pixel_y_max = (self.max_y - self.center_y) * self.scale + height / 2

        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(3*width / 4, pixel_y_min, 3*width / 4, pixel_y_max)

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        for y in range(int(self.limits[2]*10), int(self.limits[3]*10) + 1):
            pixel_y = (y/10 - self.center_y) * self.scale + height / 2
            
            if y % 10 == 0:
                tick_width = 10
                # Dibujar etiqueta
                painter.save()
                painter.translate(width / 2 - 20, pixel_y + 5)
                painter.rotate(-90)
                painter.drawText(0, 0, 40, 20, Qt.AlignCenter, str(y))
                painter.restore()
            elif y % 5 == 0:
                tick_width = 8
            else:
                tick_width = 5
                
            painter.drawLine(3*width / 4, pixel_y, 
                            3*width / 4 - tick_width, pixel_y)

    def render_plate(self, plate, is_dark_mode):
        """Renderiza la placa a una imagen QImage para usar en QGraphicsView"""
        if plate is None or plate.get_number_atoms() == 0:
            return QImage()
        
        # Crear una imagen temporal para renderizar
        width = self.drawing_area.width()
        height = self.drawing_area.height()
        image = QImage(width, height, QImage.Format_RGB888)
        
        # Configurar painter temporal
        temp_painter = QPainter(image)
        self.update_plate_metrics()
        
        # Configurar transformación
        temp_painter.save()
        temp_painter.scale(self.scale, self.scale)
        temp_painter.translate(width / (2 * self.scale) - self.center_x, 
                              height / (2 * self.scale) - self.center_y)

        # Dibujar fondo
        if is_dark_mode:
            temp_painter.fillRect(QRectF(-1000, -1000, 2000, 2000), QColor(30, 30, 30))
        else:
            temp_painter.fillRect(QRectF(-1000, -1000, 2000, 2000), Qt.white)

        # Dibujar átomos de carbono
        if is_dark_mode:
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(QColor(0, 255, 255))  # Cian
        else:
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(Qt.black)
            
        for coord in plate.get_carbon_coords():
            x = coord[0]
            y = coord[1]
            temp_painter.drawEllipse(QPointF(x, y), 0.035, 0.035)

        # Dibujar óxidos
        for coord in plate.get_oxide_coords():
            x, y, _, oxide_type, _ = coord
            if oxide_type == "OO":
                temp_painter.setBrush(QColor(255, 0, 0))  # Rojo
            elif oxide_type == "OE":
                temp_painter.setBrush(QColor(0, 0, 255))  # Azul
            elif oxide_type == "HO":
                if is_dark_mode:
                    temp_painter.setBrush(QColor(200, 200, 200))  # Gris claro
                else:
                    temp_painter.setBrush(QColor(150, 150, 150))  # Gris
                    
            temp_painter.drawEllipse(QPointF(x, y), 0.025, 0.025)

        temp_painter.restore()
        temp_painter.end()
        
        return image
    