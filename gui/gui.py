from PyQt5.QtWidgets import QMainWindow, QWidget, QMessageBox, QVBoxLayout, QComboBox
from PyQt5.QtCore import QSettings, QRect, QSize, Qt
from PyQt5.QtGui import QFont

# from ui
from gui.main_window import Ui_main


class Window:
    def __init__(self, name: str, _type: str):
        if _type == "QMainWindow":
            self.window = QMainWindow()
        elif _type == 'QWidget':
            self.window = QWidget()
        self.settings = QSettings(name)
        self.__make_Window_connections()

    def show(self):
        self.window.show()

    def close(self):
        self.window.close()

    def message(self, types: str, content: str):
        if types == 'i':
            QMessageBox.information(self.window, 'Informacja', content)
        elif types == 'w':
            QMessageBox.warning(self.window, 'Ostrzeżenie', content)
        elif types == 'c':
            QMessageBox.critical(self.window, 'Błąd', content)
        elif types == 'q':
            response = QMessageBox.question(self.window, 'Question', content)
            if response == QMessageBox.Yes:
                return True
            else:
                return False

    def load_settings(self):
        geometry = self.settings.value('geometry')
        try:
            self.window.setGeometry(QRect(*geometry))
        except:
            pass

    def __make_Window_connections(self):
        self.window.closeEvent = self.closeWindow

    def closeWindow(self, event):
        actual_geometry = self.window.geometry().getRect()
        self.settings.setValue('geometry', actual_geometry)

    def auto_resize_window(self, widget: 'QWidget', remove=True):
        if remove:
            self.window.setMinimumHeight(self.window.height() - widget.height())
            self.window.setMaximumHeight(self.window.height() - widget.height())
        else:
            self.window.setMinimumHeight(self.window.height() + widget.height())
            self.window.setMaximumHeight(self.window.height() + widget.height())


class Main(Ui_main, Window):
    def __init__(self):
        super().__init__('Main', 'QWidget')
        self.setupUi(self.window)
        self.load_settings()

