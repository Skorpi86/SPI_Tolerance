import db.mysql_con as mysql_con
from db.tools import create_select_query


def get_query(**kwargs):
    """
    Łączy się z bazą mysql a następnie pobiera query z podanej database
    """
    query = kwargs.get('query')
    database = kwargs.get('database')
    db_spi = mysql_con.connect_to_mysql(database=database)
    if query:
        try:
            db_spi['cur'].execute(query)
            response = db_spi['cur'].fetchall()
        except Exception as e:
            return
    else:
        return
    return response


def get_project_names_from_spi(**kwargs):
    """
    Pobiera listę programów z SPI
    """
    query = "SHOW DATABASES"
    response = get_query(query=query)
    if response:
        projects = [project_name[0] for project_name in response if type(project_name) is tuple]
        return projects
    else:
        return []


def check_tables_list(**kwargs):
    """
    Pobiera listę tabel w wybranej bazie danych
    """
    database = kwargs.get('database')
    important_tables = kwargs.get('important_tables') if type(kwargs.get('important_tables')) is list else []
    if not (database and important_tables):
        return False

    database_schema = get_query(database=database, query=f"SHOW TABLES")
    if database_schema:
        all_tables = [x[0] for x in database_schema if len(x) > 0]
        for table_name in important_tables:
            if table_name not in all_tables:
                return False
        return True
    else:
        return False


def get_pad_info(**kwargs):
    """
    Pobiera informację z tabeli pad_info
    """
    database = kwargs.get('database')
    if not database:
        return
    conditions = ""
    chosen_components = kwargs.get('CompID')
    if chosen_components or chosen_components == 0:
        chosen_components = tuple(chosen_components) if type(chosen_components) in [list, tuple] else (
        chosen_components,)
        if len(chosen_components) == 1:
            conditions1 = f"CompID={str(chosen_components[0])}"
        elif len(chosen_components) > 1:
            conditions1 = f"CompID IN {str(chosen_components)}"
        else:
            conditions1 = False
    else:
        conditions1 = False
    conditions += conditions1 if conditions1 else conditions
    columns = ['BoardID', 'PadID', 'CompID', 'PadName', 'HeightUSL', 'HeightLSL', 'AreaUSL', 'AreaLSL', 'VolumeUSL', 'VolumeLSL', 'IsNoUse', 'IsInspHeight', 'IsInspArea', 'IsInspVolume', 'IsInspOffset', 'IsInspBridge', 'BridgeInspDir', 'BridgeDetectH', 'BridgeDetectL', 'OffsetXSpec', 'OffsetYSpec']
    table_name = "pad_info"
    if not columns:
        table_schema = get_query(database=database, query=f"SHOW COLUMNS from {table_name}")
        if table_schema:
            columns = [x[0] for x in table_schema if len(x) > 0]
    if not columns:
        return []
    query = create_select_query(columns=columns, table_name=table_name, conditions=conditions)
    response = get_query(database=database, query=query)
    pad_info = []
    if response:
        for row in response:
            pad_info_row = {}
            for i, column_name in enumerate(columns):
                pad_info_row.update({column_name: row[i]})
            pad_info.append(pad_info_row)
        return pad_info
    else:
        return []


def update_pad_info(**kwargs):
    database = kwargs.get('database')
    pad_info_new = kwargs.get('pad_info')
    progressBar = kwargs.get('progressBar')
    db_spi = mysql_con.connect_to_mysql(database=database)
    if pad_info_new:
        try:
            for row in pad_info_new:
                correct_tolerance = row['correct_tolerance']
                values = ', '.join([f"{k}={v}" for k, v in correct_tolerance.items() if k != 'PadID'])
                conditions = row['conditions']
                query = f"UPDATE pad_info SET {values} WHERE {conditions}"
                db_spi['cur'].execute(query)
                if progressBar is not None:
                    progressBar['actual'] += 1
        except Exception as e:
            return False
        db_spi['con'].commit()
        return True
    else:
        return False


def get_comp_info(**kwargs):
    """
    Pobiera informację z tabeli comp_info
    """
    database = kwargs.get('database')
    if not database:
        return False
    chosen_components = kwargs.get('CompName')
    conditions = ""
    if chosen_components:
        chosen_components = tuple(chosen_components) if type(chosen_components) in [list, tuple] else (chosen_components,)
        if len(chosen_components) == 1:
            conditions1 = f"CompName='{str(chosen_components[0])}'"
        elif len(chosen_components) > 1:
            conditions1 = f"CompName IN {str(chosen_components)}"
        else:
            conditions1 = False
    else:
        conditions1 = False
    conditions += conditions1 if conditions1 else conditions
    columns = ["CompID", "CompName"]
    table_name = "comp_info"
    query = create_select_query(columns=columns, table_name=table_name, conditions=conditions)
    response = get_query(database=database, query=query)
    comp_info = []
    if response:
        for row in response:
            comp_info_row = {}
            for i, column_name in enumerate(columns):
                comp_info_row.update({column_name: row[i]})
            comp_info.append(comp_info_row)
        return comp_info
    else:
        return False

