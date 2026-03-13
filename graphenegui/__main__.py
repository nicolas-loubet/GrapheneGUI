from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from .logic.main_window import MainWindow
import sys
import traceback

_error_dialog_shown= False

def show_error_dialog(exc_type, exc_value, exc_traceback):
    global _error_dialog_shown
    if _error_dialog_shown: return
    _error_dialog_shown = True

    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    dialog = QMessageBox()
    dialog.setWindowTitle("GrapheneGUI Error")
    dialog.setText(f"An error occurred:\n{exc_value}")
    print(error_message)
    dialog.setDetailedText(error_message)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setStandardButtons(QMessageBox.Ok)

    dialog.exec()

    app = QApplication.instance()
    if app is not None:
        app.quit()

def main():
    app = QApplication([])

    import graphenegui.ui.resources_rc  # Registra recursos después de QApplication

    svg_icon = QIcon(":/icons/img/svg/icon.svg")
    icon = svg_icon if not svg_icon.isNull() else QIcon(":/icons/img/png/icon.png")
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    app.exec()

if __name__ == "__main__":
    sys.excepthook = show_error_dialog
    main()
