import json


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



















