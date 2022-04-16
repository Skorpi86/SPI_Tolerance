
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from gui.gui import Main

from db.SPI_data import DataFromSPI
from db.tools import load_json


class App:
    def __init__(self):
        self.MySQL_Thread = MySQL_Thread()
        self.main = Main()
        self.main.window.setWindowTitle('SPI Tolerance [ v0.1 ][20220416]')
        self.app_config = load_json('app_config.json')
        self.current_tolerance = {}
        self.data_from_spi = DataFromSPI(app_config=self.app_config)
        self.run_app()

    def run_app(self):
        self.app_connection()
        try:
            program_list = self.data_from_spi.get_program_list()
        except Exception as e:
            program_list = []
            self.main.message('c', "Brak połączenia z SPI !!!")
        if program_list:
            self.main.list_get_tolerance_from.addItems(program_list)
            self.main.list_set_tolerance_to.addItems(program_list)
            self.main.list_projet_name_library.addItems(program_list)
            self.add_CompName_to_components_list()
            self.MySQL_Thread.data_from_spi = self.data_from_spi
        self.main.show()

    def app_connection(self):
        self.main.list_projet_name_library.currentIndexChanged.connect(self.add_CompName_to_components_list)
        self.main.checkBox_CompName_library.stateChanged.connect(self.add_CompName_to_components_list)
        self.main.btn_synchronize.clicked.connect(self.synchronize_tolerance_between_projects)
        self.main.btn_update_from_library.clicked.connect(self.synchronize_tolerance_between_project_and_library)
        self.MySQL_Thread.finished.connect(self.mysql_update)

    def add_CompName_to_components_list(self):
        database = self.main.list_projet_name_library.currentText()
        self.main.CompName.clear()
        components = self.data_from_spi.get_CompName(database=database)
        for CompName in components:
            self.main.CompName.addItem(CompName, status=self.main.checkBox_CompName_library.isChecked())

    def synchronize_tolerance_between_projects(self):
        self.lock_app(True)
        self.main.text_logs.clear()
        self.MySQL_Thread.project_name_with_correct_tolerance = self.main.list_get_tolerance_from.currentText()
        self.MySQL_Thread.new_project_name = self.main.list_set_tolerance_to.currentText()
        self.MySQL_Thread.start()

    def synchronize_tolerance_between_project_and_library(self):
        choosen_components = self.get_components_from_list()
        print(choosen_components)

    def get_components_from_list(self):
        return [self.main.CompName.itemText(x) for x in range(self.main.CompName.count()) if self.main.CompName.itemChecked(x) is True]

    def mysql_update(self, data):
        if data.get("message"):
            self.main.message(f"{data['message'][0]}", data['message'][1])
        if data.get("update status"):
            self.main.text_logs.append(f"Komponenty wybrane do aktualizacji:\n{', '.join(data['update status']['CompName'])}")
            if data['update status']['STATUS']:
                self.main.text_logs.append('\n'.join(data['update status']['Tolerance']))
                self.main.message('i', f"Pomyślnie zaktualizowano tolerancje pomiędzy projektami ({data['update status']['Statistic'].get('Changed')}/{data['update status']['Statistic'].get('All')}).")
            else:
                self.main.message('w', 'Błąd podczas aktualizacji komponentów!!!')
        self.lock_app(False)

    def lock_app(self, status):
        self.main.list_get_tolerance_from.setDisabled(status)
        self.main.list_set_tolerance_to.setDisabled(status)
        self.main.tab_2.setDisabled(status)
        self.main.btn_synchronize.setDisabled(status)


class MySQL_Thread(QThread):
    finished = pyqtSignal(object)
    data_from_spi = None
    project_name_with_correct_tolerance = ""
    new_project_name = ""
    components = []
    tolerance_from_library = []
    board_informations = None

    def run(self) -> None:
        if self.project_name_with_correct_tolerance == self.new_project_name:
            self.finished.emit({"message": ("i", "Kopiowanie do tego samego projektu nie przyniesie rezultatu.")})
            return

        self.data_from_spi.copy_pad_info_to_new_project(project_name_with_correct_tolerance=self.project_name_with_correct_tolerance, new_project_name=self.new_project_name)
        self.finished.emit({"update status": self.data_from_spi.update_status})


if __name__ == '__main__':
    application = QApplication(sys.argv)
    app_class = App()
    sys.exit(application.exec_())