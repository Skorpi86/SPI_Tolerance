import copy
import pprint

from db.SPI_query import get_comp_info, get_pad_info, get_project_names_from_spi, update_pad_info
from db.mysql_con import connect_to_mysql
from db.tools import comp_code_fixer, compare_components


class DataFromSPI:
    def __init__(self, **kwargs):
        self.app_config = kwargs.get('app_config')
        self.SPI_status = False
        self.buffer = {}
        self.update_status = {"CompName": [],
                              "Statistic": {},
                              "Tolerance": [],
                              "STATUS": 0}
        self.check_connection_to_SPI()

    def check_connection_to_SPI(self):
        SPI = connect_to_mysql()
        if SPI['con']:
            self.SPI_status = True
        else:
            self.SPI_status = False

    def get_program_list(self):
        return get_project_names_from_spi(app_config=self.app_config)

    def prepare_comp_info(self, **kwargs):
        database = kwargs.get('database')
        if not database:
            return False
        if self.buffer.get(database):
            comp_info = self.buffer[database].get("comp_info")
            if comp_info:
                return comp_info
        comp_info_original = get_comp_info(database=database)
        if not comp_info_original:
            return False
        comp_info = {
            "Project Name": database,
            "CompName": {},
            "CompID": {},
            "CompCode": {},
            "comp_info_original": comp_info_original}
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
        if not database:
            return False
        if self.buffer.get(database):
            pad_info = self.buffer[database].get("pad_info")
            if pad_info:
                return pad_info
        pad_info_original = get_pad_info(database=database)
        if not pad_info_original:
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
        project_info = kwargs.get('project_info')
        comp_info = {}
        pad_info = {}

        if not project_info:
            comp_info = self.prepare_comp_info(database=database)
            pad_info = self.prepare_pad_info(database=database)
        elif project_info:
            if not project_info.get("comp_info"):
                comp_info = self.prepare_comp_info(database=database)
            else:
                if project_info["comp_info"].get("Project Name") != database:
                    comp_info = self.prepare_comp_info(database=database)
            if not project_info.get("pad_info"):
                pad_info = self.prepare_pad_info(database=database)
            else:
                if project_info["pad_info"].get("Project Name") != database:
                    pad_info = self.prepare_pad_info(database=database)

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
        project_name_with_correct_tolerance = kwargs.get("project_name_with_correct_tolerance")
        new_project_name = kwargs.get("new_project_name")
        project_info_with_correct_tolerance = self.get_project_info(database=project_name_with_correct_tolerance)
        project_info_new_project = self.get_project_info(database=new_project_name)
        if project_info_with_correct_tolerance and project_info_new_project:
            pad_info_to_update = self.set_tolerance_in_the_same_CompName(project_with_correct_tolerance=project_info_with_correct_tolerance, new_project=project_info_new_project)
            self.update_status['STATUS'] = update_pad_info(database=new_project_name, pad_info=pad_info_to_update)

    def get_the_same_CompName(self, project_with_correct_tolerance, new_project):
        CompName_with_correct_tolerance = project_with_correct_tolerance["comp_info"]["CompID"].keys()
        all_CompName = new_project["comp_info"]["CompID"].keys()
        self.update_status['Statistic'].update({"All": len(all_CompName)})
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
                return {}
        else:
            return {}

    def set_tolerance_in_the_same_CompName(self, project_with_correct_tolerance, new_project):
        the_same_CompName = self.get_the_same_CompName(project_with_correct_tolerance=project_with_correct_tolerance, new_project=new_project)
        pad_info_to_update = []
        if not the_same_CompName["CompName"]:
            return pad_info_to_update
        verifed_CompName = []
        for row in new_project["pad_info"]["pad_info_original"]:
            CompName = new_project["comp_info"]["CompName"][row["CompID"]]
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
            pad_info_to_update.append({
                'conditions': f"BoardID={row['BoardID']} AND CompID={row['CompID']} AND PadName=\'{row['PadName']}\'",
                'correct_tolerance': correct_tolerance
            })
            self.prepare_tolerance_to_show_in_logs(BoardID=row['BoardID'], CompName=CompName, PadName=row['PadName'], original=row, new=correct_tolerance)
        self.update_status["CompName"] = verifed_CompName.copy()
        self.update_status['Statistic'].update({"Changed": len(verifed_CompName)})
        return pad_info_to_update

    def clear_update_status(self):
        for k in self.update_status.keys():
            if k == 'STATUS':
                self.update_status[k] = False
                continue
            self.update_status[k].clear()

    def prepare_tolerance_to_show_in_logs(self, BoardID, CompName, PadName, original, new):
        if not self.update_status['Tolerance']:
            self.update_status['Tolerance'].append(f"""
Raport z aktualizacji:
{'BoardID'}\t{'CompName'}\t{'PadName'}\t{'HeightLSL'}\t{'HeightUSL'}\t{'AreaLSL'}\t{'AreaUSL'}\t{'VolumeLSL'}\t{'VolumeUSL'}""")
        self.update_status['Tolerance'].append(f"""
{BoardID}\t{CompName}\t{PadName}\t{original['HeightLSL']} | {new['HeightLSL']}\t{original['HeightUSL']} | {new['HeightUSL']}\t{original['AreaLSL']} | {new['AreaLSL']}\t{original['AreaUSL']} | {new['AreaUSL']}\t{original['VolumeLSL']} | {new['VolumeLSL']}\t{original['VolumeUSL']} | {new['VolumeUSL']}""")








