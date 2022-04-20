import math
import json
import re

def comp_code_fixer(CompCode):
    pattern = r'^PART[0-9]+'
    if CompCode:
        if re.search(pattern, CompCode):
            return "DEFAULT_PART"
        else:
            return CompCode
    return ""


def get_table_name(**kwargs):
    """
    InspPanelIndex - tuple, list indexów paneli dla których chcemy poznać nazwy tabel w których się znajdują dane
    -> dict - table_names[table_name] = [panel] (jeden index lub lista indexów)
    """
    InspPanelIndex = kwargs.get('InspPanelIndex')
    if not InspPanelIndex:
        return False
    if type(InspPanelIndex) not in [tuple, list]:
        InspPanelIndex = [InspPanelIndex]
    table_names = {}
    for InspPanelIndex_row in InspPanelIndex:
        podzielnik = math.ceil(int(InspPanelIndex_row) / 1000)
        if podzielnik <= 1:
            table_name = "pad_insp_result_1"
        else:
            table_name = f"pad_insp_result_{(podzielnik * 1000) - 999}"
        if table_names.get(table_name) is None:
            table_names[table_name] = [InspPanelIndex_row]
        else:
            table_names[table_name].append(InspPanelIndex_row)
    return table_names


def create_SQL(condition: str = None, item: list = None, **kwargs) -> str:
    if kwargs.get('column_names'):
        SQL = ", ".join(kwargs.get('column_names'))
        if not SQL:
            return False
    else:
        if not condition or not item:
            return False
        if type(item) is not tuple:
            item = tuple(item)
        if len(item) == 1:
            SQL = f"{condition}={str(item[0])}"
        elif len(item) > 1:
            SQL = f"{condition} IN {str(item)}"
        else:
            return False
    return SQL


def add_barcode_to_data(data: dict, barcode: dict):
    for key1, value1 in barcode.items():
        for key2, value2 in value1.items():
            data[key1][key2].update({'barcode': value2})


def add_panel_detail_to_data(data: dict, panel_detail: dict):
    for key1, value1 in panel_detail.items():
        data[key1].update({'panel_detail': value1})


def load_json(file_path):
    """
    Ładuje plik ze ścieżki file_path.
    Plik musi być w formacie JSON
    """
    try:
        with open(file_path) as f:
            data = json.load(f)
            return data
    except Exception as e:
        return ""


def save_json(data, file_path=None):
    """
    Zapisuje dane: data do pliku file_path.
    data musi być w formacie JSON
    """
    if type(data) == dict:
        if data.get("skip_programs"):
            file_path = 'app_config.json'
        elif data.get("host"):
            file_path = 'mysql_config.json'
    if not file_path:
        return False
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            return True
    except Exception as e:
        return False


def load_txt_css(file_path):
    """
    Ładuje plik ze ścieżki file_path.
    """
    try:
        with open(file_path) as f:
            data = f.read()
            return data
    except Exception as e:
        return ""


def create_select_query(**kwargs):
    """
    Tworzy zapytanie SQL do bazy mysql
    columns - kolumny jakie nas interesuja w danej tabeli ['xxx']
    table_name - nazwa tabeli z której chcemy pobrać informację
    coditions - warunki
    """
    columns = kwargs.get('columns')
    table_name = kwargs.get('table_name')
    coditions = kwargs.get('conditions')
    if columns and table_name:
        query = f"SELECT {', '.join(columns)} from {table_name}"
        if coditions:
            query += f" WHERE {coditions}"
        return query
    else:
        return False


def data_checker(*args, data):
    if not data or type(data) is not dict or not all(args):
        return False
    return True


def clasification(**kwargs):
    ResultCode = kwargs.get('ResultCode')
    SqueegeeDir = kwargs.get('SqueegeeDir')
    if ResultCode in ['FAIL', 'PASS', 'GOOD', 'UNKNOWN']:
        return ResultCode
    if SqueegeeDir in ['Front to Rear', 'Rear to Front']:
        return SqueegeeDir
    if ResultCode or ResultCode == 0:
        if ResultCode == 2:
            return 'FAIL'
        elif ResultCode == 3:
            return 'PASS'
        elif ResultCode == 0:
            return 'GOOD'
        else:
            return 'UNKNOWN'
    if SqueegeeDir or SqueegeeDir == 0:
        if SqueegeeDir == 0:
            return 'Front to Rear'
        else:
            return 'Rear to Front'


def compare_components(CompName, project1, project2):
    """
    :param CompName: str ['C1', 'U1', etc]
    :param project1: dict = {'Project Name': {}, 'comp_info': {}, 'pad_info': {}} - master
    :param project2: dict = {'Project Name': {}, 'comp_info': {}, 'pad_info': {}}
    :return: bool
    """
    CompID_project1 = project1["comp_info"]["CompID"][CompName]
    CompID_project2 = project2["comp_info"]["CompID"][CompName]
    pad_project1 = project1["pad_info"]["BoardID"][tuple(project1["pad_info"]["BoardID"].keys())[-1]]["CompID"][CompID_project1]["PadName"].keys()
    pad_project2 = project2["pad_info"]["BoardID"][tuple(project2["pad_info"]["BoardID"].keys())[-1]]["CompID"][CompID_project2]["PadName"].keys()
    return pad_project1 == pad_project2


def the_same_tolerance(project1, project2):
    """
    :param project1:
    :param project2:
    :return:
    """
    for k, v in project1.items():
        if k == "PadID":
            continue
        if not (project2.get(k) == v):
            return False
    return True
















