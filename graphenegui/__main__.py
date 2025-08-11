import graphenegui.ui.resources_rc # Used to register resources
from PySide6.QtWidgets import QApplication
from .logic.main_window import MainWindow

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
