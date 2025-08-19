import graphenegui.ui.resources_rc # Used to register resources
from PySide6.QtWidgets import QApplication, QMessageBox
from .logic.main_window import MainWindow
import sys
import traceback

def show_error_dialog(exc_type, exc_value, exc_traceback):
    app= QApplication.instance()
    if app is None: app = QApplication(sys.argv)
    error_message= "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    dialog= QMessageBox()
    dialog.setWindowTitle("GrapheneGUI Error")
    dialog.setText(f"An error occurred:\n{exc_value}")
    dialog.setDetailedText(error_message)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setStandardButtons(QMessageBox.Ok)
    
    dialog.exec()
    
    if app is None: sys.exit(1)

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    sys.excepthook= show_error_dialog
    main()
