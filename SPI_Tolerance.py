
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from gui.gui import Main

from db.SPI_data import DataFromSPI
from db.tools import load_json, load_txt_css


class App:
    def __init__(self):
        self.MySQL_Thread = MySQL_Thread()
        self.main = Main()
        self.main.window.setWindowTitle('SPI Tolerance [ v0.1 ][20220420]')
        self.app_config = load_json('app_config.json')
        self.app_css = load_txt_css('styles.css')
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
            components_html = ""
            if data['update status'].get('CompName'):
                components_html += f"<p>{', '.join(data['update status'].get('CompName'))}</p>"

            if data['update status']['STATUS']:
                data_html = ""
                for row in data['update status']['Tolerance']:
                    if any([row['Original']['HeightLSL'] != row['New']['HeightLSL'],
                            row['Original']['HeightUSL'] != row['New']['HeightUSL'],
                            row['Original']['AreaLSL'] != row['New']['AreaLSL'],
                            row['Original']['AreaUSL'] != row['New']['AreaUSL'],
                            row['Original']['VolumeLSL'] != row['New']['VolumeLSL'],
                            row['Original']['VolumeUSL'] != row['New']['VolumeUSL']]):
                        status = "changed"
                    else:
                        status = "unchanged"

                    data_html += f"<tr id='{status}'><td>{row['BoardID']}</td>" \
                                 f"<td>{row['CompName']}</td>" \
                                 f"<td>{row['PadName']}</td>" \
                                 f"<td>{row['Original']['HeightLSL']}</td>" \
                                 f"<td>{row['New']['HeightLSL']}</td>" \
                                 f"<td>{row['Original']['HeightUSL']}</td>" \
                                 f"<td>{row['New']['HeightUSL']}</td>" \
                                 f"<td>{row['Original']['AreaLSL']}</td>" \
                                 f"<td>{row['New']['AreaLSL']}</td>" \
                                 f"<td>{row['Original']['AreaUSL']}</td>" \
                                 f"<td>{row['New']['AreaUSL']}</td>" \
                                 f"<td>{row['Original']['VolumeLSL']}</td>" \
                                 f"<td>{row['New']['VolumeLSL']}</td>" \
                                 f"<td>{row['Original']['VolumeUSL']}</td>" \
                                 f"<td>{row['New']['VolumeUSL']}</td></tr>"
                self.main.text_logs.setHtml(self.html_schema(components=components_html, data=data_html))
                self.main.message('i', f"Pomyślnie zaktualizowano tolerancje pomiędzy projektami ({data['update status']['Statistic'].get('Changed')}/{data['update status']['Statistic'].get('All')}).")
            else:
                self.main.message('w', 'Błąd podczas aktualizacji komponentów!!!')
        self.lock_app(False)

    def lock_app(self, status):
        self.main.list_get_tolerance_from.setDisabled(status)
        self.main.list_set_tolerance_to.setDisabled(status)
        self.main.tab_2.setDisabled(status)
        self.main.btn_synchronize.setDisabled(status)

    def html_schema(self, components, data=""):
        return f"""
<html>
<head>
<style>
{self.app_css}
</style>
</head>
<body>

<h1>Komponenty wybrane do aktualizacji:</h1>
{components}
<br>
<h1>Raport z aktualizacji (oznaczone na żółto zostały zaktualizowane):</h1>
<table>
  <tr>
    <th>BoardID</th>
    <th>CompName</th>
    <th>PadName</th>
    <th>HeightLSL</th>
    <th>HeightLSL<br>(NEW)</th>
    <th>HeightUSL</th>
    <th>HeightUSL<br>(NEW)</th>
    <th>AreaLSL</th>
    <th>AreaLSL<br>(NEW)</th>
    <th>AreaUSL</th>
    <th>AreaUSL<br>(NEW)</th>
    <th>VolumeLSL</th>
    <th>VolumeLSL<br>(NEW)</th>
    <th>VolumeUSL</th>
    <th>VolumeUSL<br>(NEW)</th>
  </tr>
  {data}
</table>
</body>
</html>"""


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