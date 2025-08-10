from PySide6.QtGui import QPainter, QColor, QPen, QFont, QImage, QPixmap
from PySide6.QtCore import Qt, QPointF, QRectF


class Renderer:
    """
    Renderer robusto para GrapheneGUI.

    Cambios principales aplicados:
    - Evita usar QPainter sobre widgets fuera del contexto de paintEvent.
    - Usa `self.drawing_area.viewport()` como dispositivo de pintado para QGraphicsView.
    - Se corrigen retornos de `render_plate` para siempre devolver una QImage válida.
    - Se agrega manejo compatible de event.pos()/event.position() para distintos bindings de Qt6.
    - Se activan hints de renderizado (antialiasing).
    - Colores de fondo de paneles/reglas/espaciador fijados a #3d3d3d cuando corresponde.
    - Se protege contra divisiones por cero y casos sin placas seleccionadas.
    - Se actualiza el mouseMoveEvent para mostrar tooltips correctamente.
    """

    BG_COLOR = QColor("#3d3d3d")  # color de fondo solicitado para paneles y rulers

    def __init__(self, drawing_area, ruler_x, ruler_y, plates, cb_plates, is_dark_mode_func):
        self.drawing_area = drawing_area
        self.ruler_x = ruler_x
        self.ruler_y = ruler_y
        self.plates = plates
        self.cb_plates = cb_plates
        self.is_dark_mode_func = is_dark_mode_func

        # Parámetros de vista / coordenadas
        self.scale = 1.0
        self.center_x = 0.0
        self.center_y = 0.0
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.limits = [0.0, 0.0, 0.0, 0.0]

        # Reemplazamos paintEvent de forma segura apuntando a funciones que reciben (event)
        # Para QGraphicsView pintamos sobre el viewport (device correcto)
        self.drawing_area.paintEvent = self.on_draw_drawing_area
        self.ruler_x.paintEvent = self.on_draw_ruler_x
        self.ruler_y.paintEvent = self.on_draw_ruler_y

        # Habilitar seguimiento del mouse y conectar evento
        self.drawing_area.setMouseTracking(True)
        self.drawing_area.mouseMoveEvent = self.on_motion_notify

        # Hacer el viewport opaco para evitar efectos con estilos
        try:
            self.drawing_area.setAttribute(Qt.WA_OpaquePaintEvent, True)
        except Exception:
            pass

    # -------------------------- utilidades --------------------------
    def _event_pos_to_point(self, event):
        # Qt6 puede exponer event.position() (QPointF) o event.pos() (QPoint)
        if hasattr(event, "position"):
            p = event.position()
            return float(p.x()), float(p.y())
        else:
            p = event.pos()
            return float(p.x()), float(p.y())

    def pixel_to_nm(self, x_win, y_win):
        """Convierte coordenadas de ventana (pixeles) a nm en el sistema de la placa.
        Devuelve (None, None) si no hay placa seleccionada.
        """
        if not self.plates or self.cb_plates.currentIndex() == -1:
            return None, None

        # proteger contra escala 0
        if self.scale == 0:
            return None, None

        width = float(self.drawing_area.width())
        height = float(self.drawing_area.height())

        # x_win/y_win vienen en pixeles; la transformación inversa de la que aplicamos al pintar
        x_nm = x_win / self.scale + self.center_x - width / (2.0 * self.scale)
        y_nm = y_win / self.scale + self.center_y - height / (2.0 * self.scale)
        return x_nm, y_nm

    # -------------------------- eventos del mouse --------------------------
    def on_motion_notify(self, event):
        # Mostrar tooltip con el átomo más cercano si está cerca
        if not self.plates or self.cb_plates.currentIndex() == -1:
            # limpiar tooltip
            try:
                self.drawing_area.setToolTip("")
            except Exception:
                pass
            return

        x_px, y_px = self._event_pos_to_point(event)
        x_nm, y_nm = self.pixel_to_nm(x_px, y_px)
        if x_nm is None:
            self.drawing_area.setToolTip("")
            return

        plate = self.plates[self.cb_plates.currentIndex()]

        # Buscar átomos carbonos
        found = False
        for coord in plate.get_carbon_coords():
            x_atom, y_atom, z_atom, name, _ = coord
            # distancia en nm
            if (x_nm - x_atom) ** 2 + (y_nm - y_atom) ** 2 < 0.01:
                self.drawing_area.setToolTip(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                found = True
                break

        if not found:
            for coord in plate.get_oxide_coords():
                x_atom, y_atom, z_atom, name, _ = coord
                if (x_nm - x_atom) ** 2 + (y_nm - y_atom) ** 2 < 0.01:
                    self.drawing_area.setToolTip(f"{name}: ({x_atom*10:.2f}, {y_atom*10:.2f}, {z_atom*10:.2f})")
                    found = True
                    break

        if not found:
            self.drawing_area.setToolTip("")

    # -------------------------- métricas de placa --------------------------
    def update_plate_metrics(self):
        if not self.plates or self.cb_plates.currentIndex() == -1:
            # valores por defecto cuando no hay placa
            self.scale = 1.0
            self.min_x = self.max_x = self.min_y = self.max_y = 0.0
            self.center_x = self.center_y = 0.0
            self.limits = [0.0, 0.0, 0.0, 0.0]
            return

        plate_index = self.cb_plates.currentIndex()
        plate = self.plates[plate_index]

        width = max(1.0, float(self.drawing_area.width()))
        height = max(1.0, float(self.drawing_area.height()))

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

        plate_width = max(1e-6, self.max_x - self.min_x)
        plate_height = max(1e-6, self.max_y - self.min_y)

        self.limits = [self.min_x, self.max_x, self.min_y, self.max_y]

        # margen de 10%
        self.scale = min(width / (plate_width * 1.1), height / (plate_height * 1.1))
        if self.scale <= 0:
            self.scale = 1.0

        self.center_x = (self.min_x + self.max_x) / 2.0
        self.center_y = (self.min_y + self.max_y) / 2.0

    # -------------------------- dibujo principal --------------------------
    def on_draw_drawing_area(self, event):
        # Importante: pintar sobre el viewport del QGraphicsView para evitar errores de paintEngine
        painter = QPainter(self.drawing_area.viewport())
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            self.update_plate_metrics()

            # fondo
            if not self.plates or self.cb_plates.currentIndex() == -1:
                painter.fillRect(self.drawing_area.viewport().rect(), self.BG_COLOR)
                painter.end()
                return

            width = float(self.drawing_area.viewport().width())
            height = float(self.drawing_area.viewport().height())

            painter.save()
            painter.scale(self.scale, self.scale)
            painter.translate(width / (2.0 * self.scale) - self.center_x,
                              height / (2.0 * self.scale) - self.center_y)

            # pinta área amplia como fondo (por si se hace zoom out)
            if self.is_dark_mode_func():
                painter.fillRect(QRectF(-1000, -1000, 2000, 2000), self.BG_COLOR)
            else:
                painter.fillRect(QRectF(-1000, -1000, 2000, 2000), self.BG_COLOR)

            # seleccionar placa
            plate_index = self.cb_plates.currentIndex()
            plate = self.plates[plate_index]

            # dibujar carbonos
            if self.is_dark_mode_func():
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 255, 255))
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(Qt.black)

            for coord in plate.get_carbon_coords():
                x = coord[0]
                y = coord[1]
                painter.drawEllipse(QPointF(x, y), 0.035, 0.035)

            # dibujar oxidos
            for coord in plate.get_oxide_coords():
                x, y, _, oxide_type, _ = coord
                if oxide_type == "OO":
                    painter.setBrush(QColor(255, 0, 0))
                elif oxide_type == "OE":
                    painter.setBrush(QColor(0, 0, 255))
                elif oxide_type == "HO":
                    if self.is_dark_mode_func():
                        painter.setBrush(QColor(200, 200, 200))
                    else:
                        painter.setBrush(QColor(150, 150, 150))
                painter.drawEllipse(QPointF(x, y), 0.025, 0.025)

            painter.restore()

            # actualizar rulers
            self.ruler_x.update()
            self.ruler_y.update()

        finally:
            # asegurar que el painter termine
            if painter.isActive():
                painter.end()

    # -------------------------- rulers --------------------------
    def on_draw_ruler_x(self, event):
        painter = QPainter(self.ruler_x)
        try:
            painter.setRenderHint(QPainter.TextAntialiasing)
            # fondo
            painter.fillRect(self.ruler_x.rect(), self.BG_COLOR)

            if not self.plates or self.cb_plates.currentIndex() == -1:
                return

            width = float(self.ruler_x.width())
            height = float(self.ruler_x.height())

            # eje en pixeles para los limites actuales
            pixel_x_min = (self.min_x - self.center_x) * self.scale + width / 2.0
            pixel_x_max = (self.max_x - self.center_x) * self.scale + width / 2.0

            pen = QPen()
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(pixel_x_min, 3.0 * height / 4.0, pixel_x_max, 3.0 * height / 4.0)

            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)

            # dibujar ticks: convertimos limits (nm) a enteros en 0.1 nm -> etiquetas en unidades de 0.1 nm
            for x in range(int(self.limits[0] * 10), int(self.limits[1] * 10) + 1):
                pixel_x = (x / 10.0 - self.center_x) * self.scale + width / 2.0

                if x % 10 == 0:
                    tick_height = 10
                    painter.drawText(int(pixel_x - 15), int(height / 2), 30, 20, Qt.AlignCenter, str(x))
                elif x % 5 == 0:
                    tick_height = 8
                else:
                    tick_height = 5

                painter.drawLine(pixel_x, 3.0 * height / 4.0, pixel_x, 3.0 * height / 4.0 - tick_height)

        finally:
            if painter.isActive():
                painter.end()

    def on_draw_ruler_y(self, event):
        painter = QPainter(self.ruler_y)
        try:
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.fillRect(self.ruler_y.rect(), self.BG_COLOR)

            if not self.plates or self.cb_plates.currentIndex() == -1:
                return

            width = float(self.ruler_y.width())
            height = float(self.ruler_y.height())

            pixel_y_min = (self.min_y - self.center_y) * self.scale + height / 2.0
            pixel_y_max = (self.max_y - self.center_y) * self.scale + height / 2.0

            pen = QPen()
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(3.0 * width / 4.0, pixel_y_min, 3.0 * width / 4.0, pixel_y_max)

            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)

            for y in range(int(self.limits[2] * 10), int(self.limits[3] * 10) + 1):
                pixel_y = (y / 10.0 - self.center_y) * self.scale + height / 2.0

                if y % 10 == 0:
                    painter.save()
                    painter.translate(width / 2.0 - 20.0, pixel_y + 5.0)
                    painter.rotate(-90.0)
                    painter.drawText(0, 0, 40, 20, Qt.AlignCenter, str(y))
                    painter.restore()
                elif y % 5 == 0:
                    tick_width = 8
                else:
                    tick_width = 5

                painter.drawLine(3.0 * width / 4.0, pixel_y, 3.0 * width / 4.0 - tick_width, pixel_y)

        finally:
            if painter.isActive():
                painter.end()

    # -------------------------- render to image (offscreen) --------------------------
    def render_plate(self, plate, is_dark_mode):
        """Renderiza la placa a QImage (offscreen) y la devuelve.
        Siempre devuelve una QImage del tamaño del drawing_area.
        """
        width = max(1, int(self.drawing_area.width()))
        height = max(1, int(self.drawing_area.height()))

        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(self.BG_COLOR)

        temp_painter = QPainter(image)
        try:
            temp_painter.setRenderHint(QPainter.Antialiasing)
            self.update_plate_metrics()

            temp_painter.save()
            temp_painter.scale(self.scale, self.scale)
            temp_painter.translate(width / (2.0 * self.scale) - self.center_x,
                                   height / (2.0 * self.scale) - self.center_y)

            # fondo amplio
            temp_painter.fillRect(QRectF(-1000, -1000, 2000, 2000), self.BG_COLOR)

            # carbonos
            if is_dark_mode:
                temp_painter.setPen(Qt.NoPen)
                temp_painter.setBrush(QColor(0, 255, 255))
            else:
                temp_painter.setPen(Qt.NoPen)
                temp_painter.setBrush(Qt.black)

            for coord in plate.get_carbon_coords():
                x = coord[0]
                y = coord[1]
                temp_painter.drawEllipse(QPointF(x, y), 0.035, 0.035)

            for coord in plate.get_oxide_coords():
                x, y, _, oxide_type, _ = coord
                if oxide_type == "OO":
                    temp_painter.setBrush(QColor(255, 0, 0))
                elif oxide_type == "OE":
                    temp_painter.setBrush(QColor(0, 0, 255))
                elif oxide_type == "HO":
                    if is_dark_mode:
                        temp_painter.setBrush(QColor(200, 200, 200))
                    else:
                        temp_painter.setBrush(QColor(150, 150, 150))
                temp_painter.drawEllipse(QPointF(x, y), 0.025, 0.025)

            temp_painter.restore()

        finally:
            if temp_painter.isActive():
                temp_painter.end()

        return image
