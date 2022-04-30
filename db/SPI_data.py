import copy

from db.SPI_query import get_comp_info, get_pad_info, get_project_names_from_spi, update_pad_info, check_tables_list
from db.mysql_con import connect_to_mysql
from db.tools import compare_components, the_same_tolerance, save_json


class DataFromSPI:
    def __init__(self, **kwargs):
        self.mysql_conected = False
        self.app_config = kwargs.get('app_config')
        self.progressBar = kwargs.get('progressBar')
        self.get_from_project = {}
        self.set_in_project = {}
        self.update = {"CompName": [],
                       "statistic": {},
                       "tolerance": [],
                       'message': [],
                       "status": False}

    def check_connection_to_SPI(self):
        SPI = connect_to_mysql()
        self.mysql_conected = True if SPI['con'] else False

    def get_program_list(self, **kwargs):
        self.check_connection_to_SPI()
        good_program_name = []
        if not self.mysql_conected:
            return good_program_name
        all_programs = get_project_names_from_spi()
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

    def prepare_comp_info(self, **kwargs):
        database = kwargs.get('database')
        choosen_components = kwargs.get('CompName')
        comp_info_original = get_comp_info(database=database, CompName=choosen_components)

        assert comp_info_original, f"Project: {database}\nBłąd podczas pobierania informacji z tabeli: comp_info"

        comp_info = {
            "CompName": {},
            "CompID": {},
            "comp_info_original": comp_info_original
        }
        for row in comp_info_original:
            comp_info["CompName"].update({row['CompID']: row['CompName']})
            comp_info["CompID"].update({row['CompName']: row['CompID']})

        return comp_info

    def prepare_pad_info(self, **kwargs):
        database = kwargs.get('database')
        choosen_components = kwargs.get('CompID')
        pad_info_original = get_pad_info(database=database, CompID=choosen_components)

        assert pad_info_original, f"Project: {database}\nBłąd podczas pobierania informacji z tabeli: pad_info"

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

        return pad_info

    def get_project_info(self, database, **kwargs):
        choosen_components = kwargs.get('CompName')
        comp_info = self.prepare_comp_info(database=database, CompName=choosen_components)

        if choosen_components:
            choosen_components_id = [comp_info['comp_info']['CompID'].get(x) for x in choosen_components]
        else:
            choosen_components_id = []

        pad_info = self.prepare_pad_info(database=database, CompID=choosen_components_id)

        return {"ProjectName": database, "comp_info": comp_info, "pad_info": pad_info}

    def get_CompName(self, database):
        comp_info = self.prepare_comp_info(database=database)
        if comp_info.get('CompID'):
            CompName = tuple(comp_info['CompID'].keys())
        else:
            CompName = tuple()
        return CompName

    def copy_pad_info_to_new_project(self, **kwargs):
        self.clear_update_status()
        self.progressBar['actual'] = 0
        get_from = kwargs.get("get_from")
        set_in = kwargs.get("set_in")
        get_from_project_info = self.get_project_info(database=get_from)
        set_in_project_info = self.get_project_info(database=set_in)

        pad_info_to_update = self.set_tolerance_in_the_same_CompName(get_from_project_info=get_from_project_info, set_in_project_info=set_in_project_info)

        if not (len(pad_info_to_update) > 0):
            self.update['status'] = False
            self.update['message'] = ['i', f"Project: {set_in}\nWszystkie tolerancję były już aktualne."]

        self.update['status'] = update_pad_info(database=set_in, pad_info=pad_info_to_update, progressBar=self.progressBar)

    def get_the_same_CompName(self, get_from_project_info, set_in_project_info):
        get_from_CompName = [k for k in get_from_project_info['comp_info']['CompID'].keys() if k != '-1']
        set_in_CompName = [k for k in set_in_project_info['comp_info']['CompID'].keys() if k != '-1']
        the_same_CompName = {"get_from_CompID": {}, "set_in_CompID": {}, "CompName": []}
        if get_from_CompName and set_in_CompName:
            compare = [x for x in get_from_CompName if x in set_in_CompName]
            if compare:
                for CompName in compare:
                    if CompName == '-1':
                        continue
                    the_same_CompName["get_from_CompID"].update({CompName: get_from_project_info["comp_info"]["CompID"].get(CompName)})
                    the_same_CompName["set_in_CompID"].update({CompName: set_in_project_info["comp_info"]["CompID"].get(CompName)})
                    the_same_CompName["CompName"].append(CompName)
                return the_same_CompName
            else:
                return the_same_CompName
        else:
            return the_same_CompName

    def set_tolerance_in_the_same_CompName(self, get_from_project_info, set_in_project_info):
        the_same_CompName = self.get_the_same_CompName(get_from_project_info=get_from_project_info, set_in_project_info=set_in_project_info)
        pad_info_to_update = []
        if not the_same_CompName["CompName"]:
            return pad_info_to_update
        verifed_CompName = []
        for row in set_in_project_info["pad_info"]["pad_info_original"]:
            try:
                CompName = set_in_project_info["comp_info"]["CompName"][row["CompID"]]
            except KeyError:
                continue
            if not (CompName in the_same_CompName["CompName"]):
                continue
            if CompName not in verifed_CompName:
                if compare_components(CompName=CompName, project1=get_from_project_info, project2=set_in_project_info):
                    verifed_CompName.append(CompName)
                else:
                    continue
            if get_from_project_info["pad_info"]["BoardID"].get(row["BoardID"]):
                get_from_BoardID = row["BoardID"]
            else:
                get_from_BoardID = tuple(get_from_project_info["pad_info"]["BoardID"].keys())[-1]
            get_from_CompID = get_from_project_info["comp_info"]["CompID"][CompName]
            correct_tolerance = copy.deepcopy(get_from_project_info['pad_info']['BoardID'][get_from_BoardID]['CompID'][get_from_CompID]['PadName'][row['PadName']])
            row_to_verification = copy.deepcopy(row)
            for k in ['BoardID', 'CompID', 'PadName']:
                row_to_verification.pop(k)
            if not the_same_tolerance(project1=row_to_verification, project2=correct_tolerance):
                pad_info_to_update.append({
                    'conditions': f"BoardID={row['BoardID']} AND CompID={row['CompID']} AND PadName=\'{row['PadName']}\'",
                    'correct_tolerance': correct_tolerance
                })
            self.prepare_tolerance_to_show_in_logs(BoardID=row['BoardID'], CompName=CompName, PadName=row['PadName'], original=row, new=correct_tolerance)
        self.update["CompName"] = verifed_CompName.copy()
        self.update['statistic'].update({"Changed": len(pad_info_to_update)})
        self.update['statistic'].update({"All": len(self.update['tolerance'])})
        self.progressBar['max'] = len(pad_info_to_update) + int(0.01 * len(pad_info_to_update))
        if len(pad_info_to_update) == 0:
            self.update['status'] = True
            self.update['statistic']['Changed'] = 0
        return pad_info_to_update

    def clear_update_status(self):
        for k in self.update.keys():
            if k == 'status':
                self.update[k] = False
                continue
            self.update[k].clear()

    def prepare_tolerance_to_show_in_logs(self, BoardID, CompName, PadName, original, new):
        self.update['tolerance'].append({"BoardID": BoardID,
                                         "CompName": CompName,
                                         "PadName": PadName,
                                         "Original": original,
                                         "New": new})











