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

    def add_CompName_combobox(self, widget):
        self.CompName = CheckableComboBox()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.CompName)
        widget.setLayout(layout)
        widget.setMinimumSize(QSize(140, 20))


class Main(Ui_main, Window):
    def __init__(self):
        super().__init__('Main', 'QWidget')
        self.setupUi(self.window)
        self.add_CompName_combobox(self.widget_CompName_library)
        self.load_settings()
        self.__main_connection()

    def __main_connection(self):
        self.tabWidget.currentChanged.connect(self.__change_window_size)

    def __change_window_size(self):
        self.text_logs.clear()
        if self.tabWidget.currentIndex() == 0:
            self.window.setMinimumWidth(1050)
            self.window.setMaximumWidth(1050)
        elif self.tabWidget.currentIndex() == 1:
            self.window.setMinimumWidth(720)
            self.window.setMaximumWidth(720)



class CheckableComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self._changed = False
        font = QFont()
        font.setFamily("Calibri")
        font.setPointSize(8)
        self.setFont(font)

    def addItem(self, item, status=True):
        if status:
            checkbox = Qt.Checked
        else:
            checkbox = Qt.Unchecked
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count()-1, 0)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(checkbox)

    def itemChecked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == Qt.Checked
