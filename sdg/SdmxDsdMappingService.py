from sdg.SdmxDsdService import SdmxDsdService
from sdg.DisaggregationReportService import DisaggregationReportService
import pandas as pd
from xlsxwriter.utility import xl_range_abs
from xlsxwriter.utility import xl_rowcol_to_cell
from slugify import slugify

class SdmxDsdMappingService():

    def __init__(self, disaggregation_report_service):
        self.sdmx_dsd_service = SdmxDsdService()
        self.disaggregation_report_service = disaggregation_report_service
        self.sheet_names = []

    def create_tool(self):
        disagg_service = self.disaggregation_report_service
        sdmx_service = self.sdmx_dsd_service
        store = disagg_service.get_disaggregation_store()
        dimension_ids = sdmx_service.get_dimension_ids()

        writer = pd.ExcelWriter('sdmx-mapping-tool.xlsx', engine='xlsxwriter')
        workbook = writer.book

        validation_sheet = workbook.add_worksheet('Validation')
        validation_sheet.write(0, 0, 'SDMX Dimensions')
        for position, dimension in enumerate(dimension_ids, start=1):
            validation_sheet.write(position, 0, dimension)
            validation_sheet.write(0, position, dimension)
            code_ids = sdmx_service.get_code_ids_by_dimension(dimension)
            for row, code_id in enumerate(code_ids, start=1):
                validation_sheet.write(row, position, code_id)
            codes_range = xl_range_abs(1, position, len(code_ids), position)
            workbook.define_name(dimension, 'Validation!' + codes_range)
        dimensions_range = xl_range_abs(1, 0, len(dimension_ids), 0)
        workbook.define_name('sdmx_dimensions', 'Validation!' + dimensions_range)

        header_format = workbook.add_format({'bold': True})

        disaggregations_df = disagg_service.get_disaggregations_dataframe()
        disaggregations_df = disagg_service.remove_links_from_dataframe(disaggregations_df)
        disaggregations_df.to_excel(writer, index=False, sheet_name='Disaggregations')

        disaggregations_sheet = writer.sheets['Disaggregations']
        disaggregations_map_column = len(disaggregations_df.columns)
        disaggregations_sheet.write(0, disaggregations_map_column, 'SDMX Dimension', header_format)
        disaggregations_sheet.data_validation(1, disaggregations_map_column, 1048575, disaggregations_map_column, {
            'validate': 'list',
            'source': 'sdmx_dimensions',
        })

        for disaggregation in store:
            info = store[disaggregation]
            disaggregation_df = disagg_service.get_disaggregation_dataframe(info)
            disaggregation_sheet_name = self.get_disaggregation_sheet_name(disaggregation)
            disaggregation_df.to_excel(writer, index=False, sheet_name=disaggregation_sheet_name)

            disaggregation_sheet = writer.sheets[disaggregation_sheet_name]
            disaggregation_map_column = len(disaggregation_df.columns)
            disaggregation_sheet.write(0, disaggregation_map_column, 'SDMX Dimension', header_format)
            disaggregation_sheet.data_validation(1, disaggregation_map_column, 1048575, disaggregation_map_column, {
                'validate': 'list',
                'source': 'sdmx_dimensions',
            })
            disaggregation_sheet.write(0, disaggregation_map_column + 1, 'SDMX Code', header_format)
            disaggregation_sheet.data_validation(1, disaggregation_map_column + 1, 1048575, disaggregation_map_column + 1, {
                'validate': 'list',
                'source': 'INDIRECT(' + xl_rowcol_to_cell(1, disaggregation_map_column) + ')',
            })

        writer.save()


    def get_disaggregation_sheet_name(self, sheet_name):
        slug = slugify(sheet_name)
        if slug in self.sheet_names:
            slug = slug + '_'
        if len(slug) > 25:
            slug = slug[0:25]
        self.sheet_names.append(slug)
        return slug
