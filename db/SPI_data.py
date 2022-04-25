import copy
import pprint

from db.SPI_query import get_comp_info, get_pad_info, get_project_names_from_spi, update_pad_info, check_tables_list, create_database_library, create_table_part_number, get_part_number, insert_part_number
from db.mysql_con import connect_to_mysql
from db.tools import comp_code_fixer, compare_components, the_same_tolerance, save_json


class DataFromSPI:
    def __init__(self, **kwargs):
        self.app_config = kwargs.get('app_config')
        self.progressBar = kwargs.get('progressBar')
        self.SPI_status = False
        self.buffer = {}
        self.update_status = {"CompName": [],
                              "Statistic": {},
                              "Tolerance": [],
                              "messages": [],
                              "STATUS": 0}
        self.check_connection_to_SPI()

    def check_connection_to_SPI(self):
        SPI = connect_to_mysql()
        if SPI['con']:
            self.SPI_status = True
        else:
            self.SPI_status = False

    def get_program_list(self):
        good_program_name = []
        all_programs = get_project_names_from_spi()
        if 'library' not in all_programs:
            db_library_created = create_database_library()
            if db_library_created:
                create_table_part_number()

        skip_programs = self.get_ignore_program_list()
        save_skip_programs = False
        for program in all_programs:
            if program in skip_programs:
                continue
            else:
                if not check_tables_list(database=program, important_tables=['comp_info', 'pad_info']):
                    skip_programs.append(program)
                    save_skip_programs = True
                    continue
                else:
                    good_program_name.append(program)
        if save_skip_programs:
            self.app_config["skip_programs"] = skip_programs
            save_json(data=self.app_config)
        return good_program_name

    def get_ignore_program_list(self):
        skip_programs = []
        if self.app_config:
            if self.app_config.get("skip_programs"):
                skip_programs = self.app_config.get("skip_programs") if self.app_config.get("skip_programs") is not None else []
        return skip_programs

    def prepare_part_number_from_library(self, **kwargs):
        self.buffer['library'] = {}
        part_number = {}
        response = get_part_number()
        if response:
            for row in response:
                PartNumber = row.pop('PartNumber')
                PadName = row.pop('PadName')
                if not part_number.get(PartNumber):
                    part_number.update({PartNumber: {PadName: row}})
                elif not part_number[PartNumber].get(PadName):
                    part_number[PartNumber].update({PadName: row})
        if part_number:
            self.buffer['library'] = part_number

    def save_current_tolerance_in_library(self, PartNumber, PadName, tolerance):
        old_tolerance = {}
        if self.buffer['library'].get(PartNumber):
            old_tolerance = self.buffer['library'][PartNumber].get(PadName)
        if old_tolerance == tolerance:
            return {'message': ('i', f'W bazie danych są już takie same wartości dla:\n{PartNumber} - wyprowadzenie: {PadName}')}
        else:
            tolerance.update({'PartNumber': PartNumber, 'PadName': PadName})
            status = insert_part_number(tolerance=[tolerance])
            if status['update'][-1]:
                tolerance.pop('PartNumber')
                tolerance.pop('PadName')
                self.buffer['library'][PartNumber][PadName] = tolerance
                return {'message': ('i', f"Pomyślnie zaktualizowano wartości dla:\n{PartNumber} - wyprowadzenie: {PadName}")}
            else:
                return {'message': ('w', f"Nie udało sie zaktualizować wartości dla:\n{PartNumber} - wyprowadzenie: {PadName} !!!")}

    def prepare_comp_info(self, **kwargs):
        database = kwargs.get('database')
        choosen_components = kwargs.get('CompName')
        get_new = kwargs.get('get_new')
        if not database:
            return False
        if self.buffer.get(database) and not get_new:
            comp_info = self.buffer[database].get("comp_info")
            if comp_info:
                return comp_info
        comp_info_original = get_comp_info(database=database, CompName=choosen_components)
        if not comp_info_original:
            self.update_status['messages'].append(('w', f"Program: {database}\nBłąd podczas pobierania informacji z tabeli: comp_info"))
            return False
        comp_info = {
            "Project Name": database,
            "CompName": {},
            "CompID": {},
            "CompCode": {},
            "comp_info_original": comp_info_original
        }
        for row in comp_info_original:
            comp_info["CompName"].update({row['CompID']: row['CompName']})
            comp_info["CompCode"].update({row['CompID']: comp_code_fixer(row['CompCode'])})
            comp_info["CompID"].update({row['CompName']: row['CompID']})
        if not self.buffer.get(database):
            self.buffer.update({database: {"comp_info": comp_info}})
        else:
            self.buffer[database].update({"comp_info": comp_info})
        return comp_info

    def prepare_pad_info(self, **kwargs):
        database = kwargs.get('database')
        choosen_components = kwargs.get('CompID')
        get_new = kwargs.get('get_new')
        if not database:
            return False
        if self.buffer.get(database) and not get_new:
            pad_info = self.buffer[database].get("pad_info")
            if pad_info:
                return pad_info
        pad_info_original = get_pad_info(database=database, CompID=choosen_components)
        if not pad_info_original:
            self.update_status['messages'].append(('w', f"Program:{database}\nBłąd podczas pobierania informacji z tabeli: pad_info"))
            return False
        pad_info = {
            "Project Name": database,
            "BoardID": {},
            "pad_info_original": copy.deepcopy(pad_info_original)}
        for row in pad_info_original:
            BoardID = row.pop('BoardID')
            CompID = row.pop('CompID')
            PadID = row.pop('PadID')
            PadName = row.pop('PadName')
            PadID_row = row.copy()
            PadName_row = row.copy()
            PadID_row.update({'PadName': PadName})
            PadName_row.update({'PadID': PadID})
            if not pad_info["BoardID"].get(BoardID):
                pad_info["BoardID"].update({BoardID: {"CompID": {CompID: {'PadID': {PadID: PadID_row},
                                                                          'PadName': {PadName: PadName_row}}}}})
            elif not pad_info["BoardID"][BoardID]['CompID'].get(CompID):
                pad_info["BoardID"][BoardID]['CompID'].update({CompID: {'PadID': {PadID: PadID_row},
                                                                        'PadName': {PadName: PadName_row}}})
            else:
                pad_info["BoardID"][BoardID]['CompID'][CompID]['PadID'].update({PadID: PadID_row})
                pad_info["BoardID"][BoardID]['CompID'][CompID]['PadName'].update({PadName: PadName_row})
        if not self.buffer.get(database):
            self.buffer.update({database: {"pad_info": pad_info}})
        else:
            self.buffer[database].update({"pad_info": pad_info})
        return pad_info

    def get_project_info(self, database, **kwargs):
        choosen_components = kwargs.get('CompName')
        get_new = kwargs.get('get_new')
        comp_info = self.prepare_comp_info(database=database, get_new=get_new, CompName=choosen_components)
        if not comp_info:
            return
        choosen_components_id = [comp_info['CompID'].get(x) for x in choosen_components] if choosen_components else []
        pad_info = self.prepare_pad_info(database=database, get_new=get_new, CompID=choosen_components_id)
        if not pad_info:
            return False

        project_info = {
            'Project name': database,
            'comp_info': comp_info,
            'pad_info': pad_info
        }
        return project_info

    def get_CompName(self, database):
        comp_info = self.prepare_comp_info(database=database)
        if comp_info:
            CompName = tuple(comp_info.get('CompID').keys())
        else:
            CompName = tuple()
        return CompName

    def copy_pad_info_to_new_project(self, **kwargs):
        self.clear_update_status()
        self.progressBar['actual'] = 0
        project_name_with_correct_tolerance = kwargs.get("project_name_with_correct_tolerance")
        new_project_name = kwargs.get("new_project_name")
        project_info_with_correct_tolerance = self.get_project_info(database=project_name_with_correct_tolerance, get_new=True)
        project_info_new_project = self.get_project_info(database=new_project_name, get_new=True)
        if project_info_with_correct_tolerance and project_info_new_project:
            pad_info_to_update = self.set_tolerance_in_the_same_CompName(project_with_correct_tolerance=project_info_with_correct_tolerance, new_project=project_info_new_project)
            if len(pad_info_to_update) > 0:
                self.update_status['STATUS'] = update_pad_info(database=new_project_name, pad_info=pad_info_to_update, progressBar=self.progressBar)
            else:
                self.update_status['STATUS'] = True
                self.update_status['Statistic']['Changed'] = 0
        else:
            self.update_status['STATUS'] = False

    def get_the_same_CompName(self, project_with_correct_tolerance, new_project):
        CompName_with_correct_tolerance = project_with_correct_tolerance["comp_info"]["CompID"].keys()
        all_CompName = new_project["comp_info"]["CompID"].keys()
        the_same_CompName = {"project_with_correct_tolerance": {}, "new_project": {}, "CompName": []}
        if CompName_with_correct_tolerance and all_CompName:
            compare = [x for x in CompName_with_correct_tolerance if x in all_CompName]
            if compare:
                for CompName in compare:
                    the_same_CompName["project_with_correct_tolerance"].update({CompName: project_with_correct_tolerance["comp_info"]["CompID"].get(CompName)})
                    the_same_CompName["new_project"].update({CompName: new_project["comp_info"]["CompID"].get(CompName)})
                    the_same_CompName["CompName"].append(CompName)
                return the_same_CompName
            else:
                return the_same_CompName
        else:
            return the_same_CompName

    def set_tolerance_in_the_same_CompName(self, project_with_correct_tolerance, new_project):
        the_same_CompName = self.get_the_same_CompName(project_with_correct_tolerance=project_with_correct_tolerance, new_project=new_project)
        pad_info_to_update = []
        if not the_same_CompName["CompName"]:
            return pad_info_to_update
        verifed_CompName = []
        for row in new_project["pad_info"]["pad_info_original"]:
            try:
                CompName = new_project["comp_info"]["CompName"][row["CompID"]]
            except KeyError:
                continue
            if not (CompName in the_same_CompName["CompName"]):
                continue
            if CompName not in verifed_CompName:
                if compare_components(CompName=CompName, project1=project_with_correct_tolerance, project2=new_project):
                    verifed_CompName.append(CompName)
                else:
                    continue
            if project_with_correct_tolerance["pad_info"]["BoardID"].get(row["BoardID"]):
                BoardID_corret_tolerance = row["BoardID"]
            else:
                BoardID_corret_tolerance = tuple(project_with_correct_tolerance["pad_info"]["BoardID"].keys())[-1]
            CompID_correct_tolerance = project_with_correct_tolerance["comp_info"]["CompID"][CompName]
            correct_tolerance = project_with_correct_tolerance['pad_info']['BoardID'][BoardID_corret_tolerance]['CompID'][CompID_correct_tolerance]['PadName'][row['PadName']]
            row_to_verification = copy.deepcopy(row)
            for k in ['BoardID', 'CompID', 'PadName']:
                row_to_verification.pop(k)
            if not the_same_tolerance(project1=row_to_verification, project2=correct_tolerance):
                pad_info_to_update.append({
                    'conditions': f"BoardID={row['BoardID']} AND CompID={row['CompID']} AND PadName=\'{row['PadName']}\'",
                    'correct_tolerance': correct_tolerance
                })
            self.prepare_tolerance_to_show_in_logs(BoardID=row['BoardID'], CompName=CompName, PadName=row['PadName'], original=row, new=correct_tolerance)
        self.update_status["CompName"] = verifed_CompName.copy()
        self.update_status['Statistic'].update({"Changed": len(pad_info_to_update)})
        self.update_status['Statistic'].update({"All": len(self.update_status['Tolerance'])})
        self.progressBar['max'] = len(pad_info_to_update) + int(0.01 * len(pad_info_to_update))
        return pad_info_to_update

    def clear_update_status(self):
        for k in self.update_status.keys():
            if k == 'STATUS':
                self.update_status[k] = False
                continue
            self.update_status[k].clear()

    def prepare_tolerance_to_show_in_logs(self, BoardID, CompName, PadName, original, new):
        self.update_status['Tolerance'].append({"BoardID": BoardID,
                                                "CompName": CompName,
                                                "PadName": PadName,
                                                "Original": original,
                                                "New": new})

    def copy_part_number_tolerance_to_project(self, **kwargs):
        new_project_name = kwargs.get("new_project_name")
        choosen_components = kwargs.get("CompName")
        project_info = self.get_project_info(database=new_project_name, CompName=choosen_components, get_new=True)
        data_to_synchronization = {'save_in_library': [], 'update_project': []}
        DEFAULT_PART = get_part_number(PartNumber='DEFAULT_PART', PadName='ALL')
        for row in project_info['pad_info']['pad_info_original']:
            PartNumber = project_info['comp_info']['CompCode'].get(row['CompID'])
            if PartNumber == 'DEFAULT_PART' and DEFAULT_PART:
                part_number_tolerance = copy.deepcopy(DEFAULT_PART)
            else:
                part_number_tolerance = get_part_number(PartNumber=PartNumber, PadName=row['PadName'])
            if part_number_tolerance:
                part_number_tolerance.pop('PartNumber')
                part_number_tolerance.pop('PadName')
                if all([part_number_tolerance[k] == row[k] for k in part_number_tolerance.keys()]):
                    continue
                data_to_synchronization['update_project'].append({
                    'conditions': f"BoardID={row['BoardID']} AND CompID={row['CompID']} AND PadName=\'{row['PadName']}\'",
                    'correct_tolerance': part_number_tolerance
                })
            else:
                tolerance = {k: v for k, v in row.items() if k not in ['BoardID', 'PadID', 'CompID']}
                tolerance.update({'PartNumber': PartNumber})
                if PartNumber == 'DEFAULT_PART':
                    tolerance.update({'PadName': 'ALL'})
                    DEFAULT_PART = copy.deepcopy(tolerance)
                PartNumber_to_save_in_library = [x['PartNumber'] for x in data_to_synchronization['save_in_library']]
                PadName_to_save_in_library = [x['PadName'] for x in data_to_synchronization['save_in_library'] if x['PartNumber'] == PartNumber]
                if PartNumber not in PartNumber_to_save_in_library or (PartNumber in PartNumber_to_save_in_library and tolerance['PadName'] not in PadName_to_save_in_library):
                    data_to_synchronization['save_in_library'].append(tolerance)

        if data_to_synchronization['save_in_library']:
            insert_part_number(tolerance=data_to_synchronization['save_in_library'])
        if data_to_synchronization['update_project']:
            pass

    def __new_part_number(self):
        return {'AreaLSL': 20.0,
                'AreaUSL': 200.0,
                'BridgeDetectH': 80.0,
                'BridgeDetectL': 60.0,
                'BridgeInspDir': 255,
                'HeightLSL': 50.0,
                'HeightUSL': 250.0,
                'IsInspArea': 1,
                'IsInspBridge': 1,
                'IsInspHeight': 1,
                'IsInspOffset': 1,
                'IsInspVolume': 1,
                'IsNoUse': 0,
                'OffsetXSpec': 0.5,
                'OffsetYSpec': 0.5,
                'VolumeLSL': 20.0,
                'VolumeUSL': 220.0}










