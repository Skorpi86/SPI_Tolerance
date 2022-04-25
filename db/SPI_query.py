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


def create_database_library() -> bool:
    """
    Tworzy bazę danych o nazwię: library
    """
    db_spi = mysql_con.connect_to_mysql()
    try:
        query = 'CREATE DATABASE IF NOT EXISTS library'
        db_spi['cur'].execute(query)
    except:
        mysql_con.disconnect_mysql()
        return False
    db_spi['con'].commit()
    mysql_con.disconnect_mysql()
    return True


def create_table_part_number() -> bool:
    """
    Tworzy tabele: part_number w bazie library
    """
    db_spi = mysql_con.connect_to_mysql(database='library')
    try:
        query = """ CREATE TABLE IF NOT EXISTS part_number (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    PartNumber char(100) NOT NULL,
                    PadName char(50),
                    Shape char(1),
                    Pattern smallint(6),
                    PosX float,
                    PosY float,
                    SizeX float,
                    SizeY float,
                    Angle float,
                    Vertex text,
                    VertexCount int(11),
                    WeightOffsetX float,
                    WeightOffsetY float,
                    OriginalHeight float,
                    OriginalArea float,
                    Height float,
                    Area float,
                    Volume float,
                    Status int(11),
                    LocalFidIndex char(20),
                    IsNoUse tinyint(1),
                    IsInspHeight tinyint(1),
                    IsInspArea tinyint(1),
                    IsInspVolume tinyint(1),
                    IsInspOffset tinyint(1),
                    IsInspBridge tinyint(1),
                    IsInspShape tinyint(1),
                    IsInspClearance tinyint(1),
                    HeightUSL float,
                    HeightLSL float,
                    AreaUSL float,
                    AreaLSL float,
                    VolumeUSL float,
                    VolumeLSL float,
                    HeightWarning float,
                    AreaWarning float,
                    VolumeWarning float,
                    OffsetXSpec float,
                    OffsetYSpec float,
                    OffsetXWarning float,
                    OffsetYWarning float,
                    BridgeInspDir tinyint(3) unsigned,
                    BridgeDetectH float,
                    BridgeDetectL float,
                    ShapeSolderFlatness float,
                    BBTOffset float,
                    PadOffset float,
                    AlgMaskLower float,
                    AlgMaskUpper float,
                    AlgWindowSize float,
                    AlgExtendSize float,
                    AlgThreshold float,
                    AlgBaseRatio float,
                    AlgPadThreshold float,
                    AlgPadExtend float,
                    AlgHeightLimit float,
                    AlgAreaLimit float,
                    AlgVolumeLimit float,
                    OverNGHeightUSL float,
                    OverNGHeightLSL float,
                    OverNGAreaUSL float,
                    OverNGAreaLSL float,
                    OverNGVolumeUSL float,
                    OverNGVolumeLSL float,
                    OverNGOffsetXSpec float,
                    OverNGOffsetYSpec float,
                    Type int(11),
                    HeightTolUnit int(11),
                    OffsetTolUnit int(11),
                    OverNGTolType int(11),
                    HeightWarningUpper float,
                    AreaWarningUpper float,
                    VolumeWarningUpper float )"""
        db_spi['cur'].execute(query)
    except:
        mysql_con.disconnect_mysql()
        return False
    db_spi['con'].commit()
    mysql_con.disconnect_mysql()
    return True


def get_part_number(**kwargs):
    """
    Pobiera informację z tabeli part_number (library)
    """
    important_columns = ['PartNumber', 'PadName', 'HeightUSL', 'HeightLSL', 'AreaUSL', 'AreaLSL', 'VolumeUSL', 'VolumeLSL', 'IsNoUse', 'IsInspHeight', 'IsInspArea', 'IsInspVolume', 'IsInspOffset', 'IsInspBridge', 'BridgeInspDir', 'BridgeDetectH', 'BridgeDetectL', 'OffsetXSpec', 'OffsetYSpec']
    PartNumber = kwargs.get('PartNumber')
    PadName = kwargs.get('PadName')
    database = "library"
    table_name = "part_number"
    columns = kwargs.get('columns')
    conditions = ""
    if not columns:
        table_schema = get_query(database=database, query=f"SHOW COLUMNS from {table_name}")
        if table_schema:
            columns = [x[0] for x in table_schema if len(x) > 0]
    if not columns:
        return []
    if PartNumber and PadName:
        conditions = f"PartNumber='{PartNumber}' AND PadName='{PadName}'"
    query = create_select_query(columns=columns, table_name=table_name, conditions=conditions)
    response = get_query(database=database, query=query)
    part_number = []
    if response:
        for row in response:
            part_number_row = {}
            for i, column_name in enumerate(columns):
                if column_name not in important_columns:
                    continue
                part_number_row.update({column_name: row[i]})
            part_number.append(part_number_row)
        if PartNumber and PadName:
            return part_number[0]
        else:
            return part_number
    else:
        return False


def insert_part_number(**kwargs):
    """
    Zapisuje w bazie danych library tolerancję dla wskazanych PartNumber
    """
    tolerance = kwargs.get('tolerance')
    if not tolerance:
        return False
    insert = []
    update = []
    status = {'insert': [], 'update': []}
    for row in tolerance:
        actual_part_number = get_part_number(PartNumber=row['PartNumber'], PadName=row['PadName'])
        if actual_part_number:
            if actual_part_number != row:
                update.append(row)
            continue
        else:
            insert.append(row)
    status['insert'].append(len(insert))
    status['update'].append(len(update))
    if update:
        status['update'].append(update_part_number(tolerance=update))
    else:
        status['update'].append(None)
    if insert:
        try:
            column_names = ', '.join(insert[0].keys())
            values = []
            query = f"INSERT INTO part_number ({column_names}) VALUES ({'%s, ' * (len(insert[0].keys()) - 1)}%s)"
            for row in insert:
                values.append(tuple(row.values()))
            db_spi = mysql_con.connect_to_mysql(database='library')
            db_spi['cur'].executemany(query, values)
        except:
            mysql_con.disconnect_mysql()
            status['insert'].append(False)
            return status
        db_spi['con'].commit()
        mysql_con.disconnect_mysql()
        status['insert'].append(True)
        return status
    else:
        status['insert'].append(None)
        return status


def update_part_number(**kwargs):
    tolerance = kwargs.get('tolerance')
    db_spi = mysql_con.connect_to_mysql(database='library')
    try:
        for row in tolerance:
            values = ', '.join([f"{k}={v}" for k, v in row.items() if k not in ['PartNumber', 'PadName']])
            conditions = f"PartNumber='{row['PartNumber']}' AND PadName='{row['PadName']}'"
            query = f"UPDATE part_number SET {values} WHERE {conditions}"
            db_spi['cur'].execute(query)
    except Exception as e:
        mysql_con.disconnect_mysql()
        return False
    db_spi['con'].commit()
    mysql_con.disconnect_mysql()
    return True


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
    columns = ["CompID", "CompName", "CompCode"]
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
        return False
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
