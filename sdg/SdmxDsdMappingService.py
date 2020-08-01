from sdg.SdmxDsdService import SdmxDsdService
from sdg.DisaggregationReportService import DisaggregationReportService
import pandas as pd
from xlsxwriter.utility import xl_range_abs
from xlsxwriter.utility import xl_rowcol_to_cell
from slugify import slugify
import os

class SdmxDsdMappingService():

    def __init__(self, disaggregation_report_service, folder='_site', max_codes=1000, language='en'):
        self.sdmx_dsd_service = SdmxDsdService()
        self.disaggregation_report_service = disaggregation_report_service
        self.folder = folder
        self.max_codes = max_codes
        self.language = language
        self.sheet_names = []

    def create_tool(self):
        disagg_service = self.disaggregation_report_service
        sdmx_service = self.sdmx_dsd_service
        store = disagg_service.get_disaggregation_store()
        dimension_ids = sdmx_service.get_dimension_ids()

        excel_path = os.path.join(self.folder, 'sdmx-mapping-tool.xlsx')
        writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True
        })
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'yellow'
        })
        global_format = workbook.add_format({
            'fg_color': 'yellow'
        })
        global_header_format = workbook.add_format({
            'bold': True,
            'fg_color': 'yellow'
        })

        global_sheet = workbook.add_worksheet('CODES')
        global_sheet.merge_range('A1:P1', 'Codes - do not change yellow cells - add national codes as needed', merge_format)
        global_sheet.write(1, 0, 'Dimensions', global_header_format)
        dimension_header_row = 1
        dimension_list_column = 0
        for index, dimension_id in enumerate(dimension_ids, start=1):
            global_sheet.write(index + 1, 0, dimension_id, global_format)
            column = (index * 2) - 1
            global_sheet.write(1, column, dimension_id, global_header_format)
            global_sheet.write(1, column + 1, 'Name', global_header_format)
            codes = sdmx_service.get_codes_by_dimension_id(dimension_id)
            for row, code in enumerate(codes, start=2):
                code_id = self.sdmx_dsd_service.get_code_id(code)
                code_name = self.sdmx_dsd_service.get_code_name(code, language=self.language)
                global_sheet.write(row, column, code_id, global_format)
                global_sheet.write(row, column + 1, code_name, global_format)
            codes_range = xl_range_abs(2, column + 1, self.max_codes, column + 1)
            workbook.define_name(dimension_id, 'CODES!' + codes_range)

        global_sheet.write(len(dimension_ids) + 2, 0, '[REMOVE]')
        dimensions_range = xl_range_abs(2, 0, len(dimension_ids) + 2, 0)
        workbook.define_name('dimensions', 'CODES!' + dimensions_range)
        global_sheet.set_column('A:AE', 10)

        sorted_disaggregations = list(store.keys())
        sorted_disaggregations.sort()
        for disaggregation in sorted_disaggregations:
            info = store[disaggregation]
            disaggregation_df = disagg_service.get_disaggregation_dataframe(info)
            del disaggregation_df['Number of indicators']
            del disaggregation_df['Disaggregation combinations using this value']
            disaggregation_df = disagg_service.remove_links_from_dataframe(disaggregation_df)
            disaggregation_sheet_name = self.get_disaggregation_sheet_name(disaggregation)
            disaggregation_df.to_excel(writer, startrow=1, index=False, sheet_name=disaggregation_sheet_name)

            disaggregation_sheet = writer.sheets[disaggregation_sheet_name]
            disaggregation_map_column = len(disaggregation_df.columns)
            disaggregation_header_range = xl_range_abs(0, 0, 0, disaggregation_map_column + 3)
            disaggregation_sheet.merge_range(disaggregation_header_range, disaggregation, merge_format)
            disaggregation_sheet.write(1, disaggregation_map_column, 'Dimension 1', header_format)
            disaggregation_sheet.data_validation(2, disaggregation_map_column, self.max_codes, disaggregation_map_column, {
                'validate': 'list',
                'source': 'dimensions',
            })
            disaggregation_sheet.write(1, disaggregation_map_column + 1, 'Code 1', header_format)
            disaggregation_sheet.data_validation(2, disaggregation_map_column + 1, self.max_codes, disaggregation_map_column + 1, {
                'validate': 'list',
                'source': 'INDIRECT(' + xl_rowcol_to_cell(2, disaggregation_map_column) + ')',
            })
            disaggregation_sheet.write(1, disaggregation_map_column + 2, 'Dimension 2 (optional)', header_format)
            disaggregation_sheet.data_validation(2, disaggregation_map_column + 2, self.max_codes, disaggregation_map_column + 2, {
                'validate': 'list',
                'source': 'dimensions',
            })
            disaggregation_sheet.write(1, disaggregation_map_column + 3, 'Code 2 (optional)', header_format)
            disaggregation_sheet.data_validation(2, disaggregation_map_column + 3, self.max_codes, disaggregation_map_column + 3, {
                'validate': 'list',
                'source': 'INDIRECT(' + xl_rowcol_to_cell(2, disaggregation_map_column + 2) + ')',
            })
            disaggregation_sheet.set_column('A:Z', 30)
            disaggregation_sheet.set_row(1, 20, global_header_format)


        writer.save()


    def get_disaggregation_sheet_name(self, sheet_name):
        slug = slugify(sheet_name)
        if slug in self.sheet_names:
            slug = slug + '_'
        if len(slug) > 25:
            slug = slug[0:25]
        self.sheet_names.append(slug)
        return slug
