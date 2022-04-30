import time
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal

from gui.gui import Main

from db.SPI_data import DataFromSPI
from db.tools import load_json, load_txt_css


class App:
    def __init__(self):
        self.MySQL_Thread = MySQL_Thread()
        self.ProgressBar_Thread = ProgressBar_Thread()
        self.main = Main()
        self.main.window.setWindowTitle('SPI Tolerance [ v0.2 ][20220430]')
        self.app_config = load_json('app_config.json')
        self.app_css = load_txt_css('styles.css')
        self.current_tolerance = {}
        self.progressBar = {"max": 100, "actual": 0}
        self.data_from_spi = DataFromSPI(app_config=self.app_config, progressBar=self.progressBar)
        self.run_app()

    def run_app(self):
        self.app_connection()
        self.clear_progressBar()
        self.ProgressBar_Thread.progressBar = self.progressBar
        self.ProgressBar_Thread.start()
        self.MySQL_Thread.data_from_spi = self.data_from_spi
        program_list = self.data_from_spi.get_program_list()

        if program_list:
            self.main.get_from.addItems(program_list)
            self.main.set_in.addItems(program_list)
        self.main.show()

    def app_connection(self):
        self.main.btn_synchronize.clicked.connect(self.synchronize_tolerance)
        self.MySQL_Thread.finished.connect(self.mysql_update)
        self.ProgressBar_Thread.actual.connect(self.update_progressBar)
        self.ProgressBar_Thread.max.connect(self.set_max_value_in_progressBar)

    def synchronize_tolerance(self):
        self.lock_app(True)
        self.main.raport.clear()
        self.MySQL_Thread.get_from = self.main.get_from.currentText()
        self.MySQL_Thread.set_in = self.main.set_in.currentText()
        self.MySQL_Thread.start()

    def mysql_update(self, data):
        if data.get("message"):
            self.main.message(data['message'][0], data['message'][1])
        if data.get("update"):
            components_html = ""
            if data['update'].get('CompName'):
                components_html += f"<p>{', '.join(data['update'].get('CompName'))}</p>"

            if data['update']['status']:
                data_html = ""
                for row in data['update']['tolerance']:
                    status_dict = {'HeightLSL': row['Original']['HeightLSL'] != row['New']['HeightLSL'],
                                   'HeightUSL': row['Original']['HeightUSL'] != row['New']['HeightUSL'],
                                   'AreaLSL': row['Original']['AreaLSL'] != row['New']['AreaLSL'],
                                   'AreaUSL': row['Original']['AreaUSL'] != row['New']['AreaUSL'],
                                   'VolumeLSL': row['Original']['VolumeLSL'] != row['New']['VolumeLSL'],
                                   'VolumeUSL': row['Original']['VolumeUSL'] != row['New']['VolumeUSL']}
                    if any(status_dict.values()):
                        status = "changed"
                    else:
                        status = "unchanged"

                    data_html += f"<tr class='{status}'>"

                    for column_name in ['BoardID', 'CompName', 'PadName']:
                        data_html += f"<td>{row[column_name]}</td>"

                    for column_name in ['HeightLSL', 'HeightUSL', 'AreaLSL', 'AreaUSL', 'VolumeLSL', 'VolumeUSL']:
                        column_status = status_dict.get(column_name)
                        if column_status:
                            data_html += f"<td class='old_value'>{row['Original'][column_name]}</td>"
                            data_html += f"<td class='new_value'>{row['New'][column_name]}</td>"
                        else:
                            data_html += f"<td>{row['Original'][column_name]}</td>"
                            data_html += f"<td>{row['New'][column_name]}</td>"

                    data_html += "</tr>"
                self.main.raport.setHtml(self.html_schema(components=components_html, data=data_html))
                self.progressBar['actual'] = self.progressBar['max']
                self.main.message('i', f"Pomyślnie zaktualizowano tolerancje pomiędzy projektami ({data['update']['statistic'].get('Changed')}/{data['update']['statistic'].get('All')}).")
            else:
                if data['update'].get('message'):
                    self.main.message(data['update']['message'][0], data['update']['message'][1])
                else:
                    self.main.message('w', 'Błąd podczas aktualizacji komponentów!!!')

        self.clear_progressBar()
        self.lock_app(False)

    def lock_app(self, status, **kwargs):
        self.main.get_from.setDisabled(status)
        self.main.set_in.setDisabled(status)
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
<h1>Raport z aktualizacji (oznaczone na zielono zostały zaktualizowane):</h1>
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

    def update_progressBar(self, value):
        self.main.progressBar.setValue(value)

    def set_max_value_in_progressBar(self, value):
        self.main.progressBar.setMaximum(value)

    def clear_progressBar(self):
        self.main.progressBar.setValue(0)
        self.main.progressBar.setMaximum(100)
        self.progressBar['max'] = 100
        self.progressBar['actual'] = 0


class MySQL_Thread(QThread):
    finished = pyqtSignal(object)
    data_from_spi = None
    get_from = ""
    set_in = ""
    components = []
    board_informations = None

    def run(self) -> None:
        if self.get_from == self.set_in:
            if self.get_from == "":
                return
            self.finished.emit({"message": ("i", "Kopiowanie do tego samego projektu nie przyniesie rezultatu.")})
            return
        try:
            self.data_from_spi.copy_pad_info_to_new_project(get_from=self.get_from,
                                                            set_in=self.set_in)
            self.finished.emit({"update": self.data_from_spi.update})
        except Exception as e:
            self.finished.emit({"message": ("w", f"Błąd podczas synchronizacji komponentów!!!\n{e}")})


class ProgressBar_Thread(QThread):
    max = pyqtSignal(int)
    actual = pyqtSignal(int)
    progressBar = {}
    current_max = 0
    current_actual = 0

    def run(self) -> None:
        while True:
            if self.progressBar.get('actual') < 10 and self.current_max != self.progressBar.get('max'):
                self.current_max = self.progressBar.get('max')
                self.max.emit(self.progressBar.get('max'))

            if self.current_actual != self.progressBar.get('actual'):
                self.current_actual = self.progressBar.get('actual')
                self.actual.emit(self.progressBar.get('actual'))

            time.sleep(0.01)


if __name__ == '__main__':
    application = QApplication(sys.argv)
    app_class = App()
    sys.exit(application.exec_())