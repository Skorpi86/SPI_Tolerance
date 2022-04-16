import pprint

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
    from_json = kwargs.get("app_config")
    query = "SHOW DATABASES"
    response = get_query(query=query)
    if response:
        if from_json:
            ignore_projects = from_json.get("skip_programs")
            if not ignore_projects:
                ignore_projects = []
        else:
            ignore_projects = []
        projects = [project_name[0] for project_name in response if type(project_name) is tuple]
        projects = [project_name for project_name in projects if project_name not in ignore_projects]
        return projects
    else:
        return []


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
    db_spi = mysql_con.connect_to_mysql(database=database)
    if pad_info_new:
        try:
            for row in pad_info_new:
                correct_tolerance = row['correct_tolerance']
                values = ', '.join([f"{k}={v}" for k, v in correct_tolerance.items() if k != 'PadID'])
                conditions = row['conditions']
                query = f"UPDATE pad_info SET {values} WHERE {conditions}"
                db_spi['cur'].execute(query)
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
        return
    columns = ["CompID", "CompName", "CompCode"]
    table_name = "comp_info"
    query = create_select_query(columns=columns, table_name=table_name)
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
        return


def get_panel_insp_result(**kwargs):
    """
    Pobiera informację z tabeli panel_insp_result
    Przykład filtrowania po dacie: InspectDate BETWEEN '2021-12-15' AND '2022-03-15'
    """
    database = kwargs.get('database')
    date_min = kwargs.get('date_min')
    date_max = kwargs.get('date_max')
    chosen_panels = kwargs.get('InspPanelIndex')
    conditions = ""
    if date_min and date_max:
        conditions_1 = f"InspectDate BETWEEN '{str(date_min)}' AND '{str(date_max)}'"
    else:
        conditions_1 = False
    if conditions_1:
        conditions += conditions_1
    if chosen_panels or chosen_panels == 0:
        chosen_panels = tuple(chosen_panels) if type(chosen_panels) in [list, tuple] else (chosen_panels,)
        if len(chosen_panels) == 1:
            conditions_2 = f"InspPanelIndex={str(chosen_panels[0])}"
        elif len(chosen_panels) > 1:
            conditions_2 = f"InspPanelIndex IN {str(chosen_panels)}"
        else:
            conditions_2 = False
    else:
        conditions_2 = False
    if conditions_2:
        if conditions_1:
            conditions += " AND"
        conditions += conditions_2
    if not database:
        return
    columns = ["InspPanelIndex", "InspectDate", "ResultCode", "OperatorID", "SqueegeeDir"]
    table_name = "panel_insp_result"
    query = create_select_query(columns=columns, table_name=table_name, conditions=conditions)
    response = get_query(database=database, query=query)
    panel_insp_result = []
    if response:
        for row in response:
            panel_insp_result_row = {}
            for i, column_name in enumerate(columns):
                panel_insp_result_row.update({column_name: row[i]})
            panel_insp_result.append(panel_insp_result_row)
        return panel_insp_result


def get_board_insp_value(**kwargs):
    database = kwargs.get('database')
    seria_numbers = kwargs.get('BarcodeData')
    chosen_panels = kwargs.get('InspPanelIndex')
    boards = kwargs.get('BoardID')
    conditions = ""
    if seria_numbers:
        seria_numbers = tuple(seria_numbers) if type(seria_numbers) in [list, tuple] else (seria_numbers,)
        if len(seria_numbers) == 1:
            conditions_1 = f" BarcodeData='{str(seria_numbers[0])}'"
        elif len(seria_numbers) > 1:
            conditions_1 = f" BarcodeData IN {str(seria_numbers)}"
        else:
            conditions_1 = False
    else:
        conditions_1 = False
    if conditions_1:
        conditions += conditions_1
    if chosen_panels or chosen_panels == 0:
        chosen_panels = tuple(chosen_panels) if type(chosen_panels) in [list, tuple] else (chosen_panels,)
        if len(chosen_panels) == 1:
            conditions_2 = f" InspPanelIndex={str(chosen_panels[0])}"
        elif len(chosen_panels) > 1:
            conditions_2 = f" InspPanelIndex IN {str(chosen_panels)}"
        else:
            conditions_2 = False
    else:
        conditions_2 = False
    if conditions_2:
        if conditions_1:
            conditions += " AND"
        conditions += conditions_2
        if boards or boards == 0:
            boards = tuple(boards) if type(boards) in [list, tuple] else (boards,)
            if len(boards) == 1:
                conditions_3 = f" BoardID={str(boards[0])}"
            elif len(chosen_panels) > 1:
                conditions_3 = f" BoardID IN {str(boards)}"
            else:
                conditions_3 = False
        else:
            conditions_3 = False
        if conditions_3:
            if conditions_2:
                conditions += " AND"
            conditions += conditions_3
    if not database:
        return
    columns = ["InspPanelIndex", "BoardID", "BarcodeData"]
    table_name = "board_insp_value"
    query = create_select_query(columns=columns, table_name=table_name, conditions=conditions)
    response = get_query(database=database, query=query)
    board_insp_value = []
    if response:
        for row in response:
            board_insp_value_row = {}
            for i, column_name in enumerate(columns):
                board_insp_value_row.update({column_name: row[i]})
            board_insp_value.append(board_insp_value_row)
        return board_insp_value


def get_pad_insp_result(**kwargs):
    """
    Pobiera informację z tabeli pad_insp_result
    """
    database = kwargs.get('database')
    table_name = kwargs.get('table_name')
    pad_insp_result = kwargs.get('pad_insp_result')
    if not pad_insp_result:
        pad_insp_result = []
    if not (database and table_name):
        return
    chosen_panels = kwargs.get('InspPanelIndex')
    if chosen_panels or chosen_panels == 0:
        chosen_panels = tuple(chosen_panels) if type(chosen_panels) in [list, tuple] else (chosen_panels,)
        if len(chosen_panels) == 1:
            conditions = f"InspPanelIndex={str(chosen_panels[0])}"
        elif len(chosen_panels) > 1:
            conditions = f"InspPanelIndex IN {str(chosen_panels)}"
        else:
            conditions = False
    else:
        conditions = False
    chosen_components = kwargs.get('CompID')
    if chosen_components or chosen_components == 0:
        chosen_components = tuple(chosen_components) if type(chosen_components) in [list, tuple] else (chosen_components,)
        if len(chosen_components) == 1:
            conditions1 = f" AND CompID={str(chosen_components[0])}"
        elif len(chosen_components) > 1:
            conditions1 = f" AND CompID IN {str(chosen_components)}"
        else:
            conditions1 = False
    else:
        conditions1 = False
    conditions += conditions1 if conditions and conditions1 else conditions
    columns = ["InspPanelIndex", "CompID", "PadID", "HeightPer", "AreaPer", "VolumePer"]
    query = create_select_query(columns=columns, table_name=table_name, conditions=conditions)
    response = get_query(database=database, query=query)
    if response:
        for row in response:
            pad_insp_result_row = {}
            for i, column_name in enumerate(columns):
                pad_insp_result_row.update({column_name: row[i]})
            pad_insp_result.append(pad_insp_result_row)
        return pad_insp_result
    else:
        return []
