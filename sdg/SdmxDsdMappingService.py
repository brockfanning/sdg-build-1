from sdg.SdmxDsdService import SdmxDsdService
from sdg.DisaggregationReportService import DisaggregationReportService
import pandas as pd
import xlsxwriter
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
        workbook = xlsxwriter.Workbook(excel_path)

        #writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        #workbook = writer.book
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

        # Write the CODES sheet.
        codes_sheet = workbook.add_worksheet('CODES')
        codes_sheet.merge_range('A1:P1', 'Codes - add national codes as needed', merge_format)
        codes_sheet.write(1, 0, 'Dimensions', header_format)
        for index, dimension_id in enumerate(dimension_ids):
            # Write the dimensions (plural) column.
            codes_sheet.write(2 + index, 0, dimension_id)
            # Write the dimension (singular) columns.
            column = ((index + 1) * 2) - 1
            codes_sheet.write(1, column, dimension_id, header_format)
            codes_sheet.write(1, column + 1, 'Name', header_format)
            codes = sdmx_service.get_codes_by_dimension_id(dimension_id)
            for row, code in enumerate(codes, start=2):
                code_id = self.sdmx_dsd_service.get_code_id(code)
                code_name = self.sdmx_dsd_service.get_code_name(code, language=self.language)
                codes_sheet.write(row, column, code_id)
                codes_sheet.write(row, column + 1, code_name)
            codes_range = xl_range_abs(2, column + 1, self.max_codes, column + 1)
            workbook.define_name(dimension_id, 'CODES!' + codes_range)

        # Add "[REMOVE]" as another dimension and bump the number of dimensions.
        num_dimensions = len(dimension_ids) + 1
        codes_sheet.write(num_dimensions, 0, '[REMOVE]')
        dimensions_range = xl_range_abs(2, 0, num_dimensions + 2, 0)
        workbook.define_name('dimensions', 'CODES!' + dimensions_range)

        # Widen the columns a bit.
        codes_sheet.set_column('A:AE', 10)


        sorted_disaggregations = list(store.keys())
        sorted_disaggregations.sort()
        for disaggregation in sorted_disaggregations:
            info = store[disaggregation]
            disaggregation_df = disagg_service.get_disaggregation_dataframe(info)
            del disaggregation_df['Number of indicators']
            del disaggregation_df['Disaggregation combinations using this value']
            disaggregation_df = disagg_service.remove_links_from_dataframe(disaggregation_df)
            disaggregation_sheet_name = self.get_disaggregation_sheet_name(disaggregation)
            disaggregation_sheet = workbook.add_worksheet(disaggregation_sheet_name)

            disaggregation_map_column = len(disaggregation_df.columns)
            disaggregation_header_range = xl_range_abs(0, 0, 0, disaggregation_map_column + 3)
            disaggregation_sheet.merge_range(disaggregation_header_range, disaggregation, merge_format)
            row = 1
            column = 0
            for header in disaggregation_df.columns:
                disaggregation_sheet.write(row, column, header, header_format)
                column += 1

            row = 2
            for index, value_row in disaggregation_df.iterrows():
                column = 0
                for header in disaggregation_df.columns:
                    disaggregation_sheet.write(row, column, value_row[header])
                    column += 1
                row += 1

            row = 1
            column = disaggregation_map_column
            disaggregation_sheet.write(row, column, 'Dimension 1', header_format)
            disaggregation_sheet.write(row, column + 1, 'Code 1', header_format)
            disaggregation_sheet.write(row, column + 2, 'Dimension 2 (optional)', header_format)
            disaggregation_sheet.write(row, column + 3, 'Code 2 (optional)', header_format)

            row = 2
            for index, value_row in disaggregation_df.iterrows():

                dimension_1_cell = xl_rowcol_to_cell(row, column)
                code_1_cell = xl_rowcol_to_cell(row, column + 1)
                dimension_2_cell = xl_rowcol_to_cell(row, column + 2)
                code_2_cell = xl_rowcol_to_cell(row, column + 3)

                disaggregation_sheet.data_validation(row, column, row, column, {
                    'validate': 'list',
                    'source': 'dimensions',
                })
                disaggregation_sheet.data_validation(row, column + 2, row, column + 2, {
                    'validate': 'list',
                    'source': 'dimensions',
                })

                array_row_1_start = 1000
                array_row_1_end = 1900
                array_row_2_start = 2000
                array_row_2_end = 2900
                array_column = row - 2
                disaggregation_sheet.write_array_formula(array_row_1_start, array_column, array_row_1_end, array_column, '{=INDIRECT(' + dimension_1_cell + ')}')
                disaggregation_sheet.write_array_formula(array_row_2_start, array_column, array_row_2_end, array_column, '{=INDIRECT(' + dimension_2_cell + ')}')

                disaggregation_sheet.data_validation(code_1_cell, {
                    'validate': 'list',
                    'source': '=' + xl_range_abs(array_row_1_start, array_column, array_row_1_end, array_column),
                })
                disaggregation_sheet.data_validation(code_2_cell, {
                    'validate': 'list',
                    'source': '=' + xl_range_abs(array_row_2_start, array_column, array_row_2_end, array_column),
                })
                row += 1
            disaggregation_sheet.set_column('A:Z', 30)
            disaggregation_sheet.set_row(1, 20, header_format)

        workbook.close()


    def get_disaggregation_sheet_name(self, sheet_name):
        slug = slugify(sheet_name)
        if slug in self.sheet_names:
            slug = slug + '_'
        if len(slug) > 25:
            slug = slug[0:25]
        self.sheet_names.append(slug)
        return slug
