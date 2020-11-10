from sdg.SdmxDsdService import SdmxDsdService
from sdg.DisaggregationReportService import DisaggregationReportService
import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_range_abs
from xlsxwriter.utility import xl_rowcol_to_cell
from slugify import slugify
from urllib.request import urlretrieve
from xml.etree import ElementTree as ET
from io import StringIO
import os

class SdmxDsdMappingService():

    def __init__(self, disaggregation_report_service, folder='_site', max_codes=1000, language='en',
                 existing_map=None):
        self.disaggregation_report_service = disaggregation_report_service
        self.folder = folder
        self.max_codes = max_codes
        self.language = language
        self.sheet_names = []
        if existing_map is not None:
            self.existing_map = self.read_mapping(existing_map)
            dsd_path = 'dsd.xml'
            self.create_dsd_from_map(dsd_path=dsd_path)
            self.sdmx_dsd_service = SdmxDsdService(dsd_path=dsd_path)
        else:
            self.existing_map = None
            self.sdmx_dsd_service = SdmxDsdService()


    def create_mapping_tool(self):
        disagg_service = self.disaggregation_report_service
        sdmx_service = self.sdmx_dsd_service
        store = disagg_service.get_disaggregation_store()
        dimension_ids = sdmx_service.get_dimension_ids()

        excel_path = os.path.join(self.folder, 'sdmx-mapping-tool.xlsx')
        workbook = xlsxwriter.Workbook(excel_path)

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

        # Add "[REMOVE]" as another dimension and bump the number of dimensions.
        num_dimensions = len(dimension_ids) + 1
        codes_sheet.write(num_dimensions, 0, '[REMOVE]')
        dimensions_range = xl_range_abs(2, 0, num_dimensions + 2, 0)
        workbook.define_name('dimensions', 'CODES!' + dimensions_range)

        # Write the UNITS sheet.
        units_sheet = workbook.add_worksheet('UNITS')
        units_sheet.merge_range('A1:P1', 'Units of measurement', merge_format)
        units_sheet.write(1, 0, 'UNIT_MEASURE', header_format)
        units_sheet.write(1, 1, 'Name', header_format)

        unit_codes = sdmx_service.get_codes_by_attribute_id('UNIT_MEASURE')
        for index, code in enumerate(unit_codes):
            code_id = self.sdmx_dsd_service.get_code_id(code)
            code_name = self.sdmx_dsd_service.get_code_name(code, language=self.language)
            units_sheet.write(2 + index, 0, code_id)
            units_sheet.write(2 + index, 1, code_name)

        num_units = len(unit_codes) + 1
        units_sheet.write(num_units + 1, 0, '[REMOVE]')
        units_sheet.write(num_units + 1, 1, '[REMOVE]')
        units_range = xl_range_abs(2, 1, num_units + 2, 1)
        workbook.define_name('units', 'UNITS!' + units_range)

        existing_units = None if self.existing_map is None else self.parse_unit_sheet()
        existing_units_dict = dict(zip(existing_units['from'], existing_units['to']))

        units_sheet.write(1, 3, 'Mapped from', header_format)
        units_sheet.write(1, 4, 'Mapped to', header_format)
        units_df = disagg_service.get_units_dataframe()
        for index, unit_row in units_df.iterrows():
            units_sheet.write(index + 2, 3, unit_row['Unit'])
            units_sheet.data_validation(index + 2, 4, index + 2, 4, {
                'validate': 'list',
                'source': 'units',
            })
            if existing_units is not None and unit_row['Unit'] in existing_units_dict:
                units_sheet.write(index + 2, 4, existing_units_dict[unit_row['Unit']])

        # Widen the columns a bit.
        units_sheet.set_column('A:E', 20)

        # Write the disaggregation sheets.
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

            existing_disaggregation = None
            if self.existing_map is not None:
                existing_disaggregation = self.parse_disaggregation_sheet(disaggregation_sheet_name)
                if existing_disaggregation is not None:
                    existing_disaggregation_dict = {
                        'dimension1': dict(zip(existing_disaggregation['value'], existing_disaggregation['dimension1'])),
                        'code1': dict(zip(existing_disaggregation['value'], existing_disaggregation['code1'])),
                        'dimension2': dict(zip(existing_disaggregation['value'], existing_disaggregation['dimension2'])),
                        'code2': dict(zip(existing_disaggregation['value'], existing_disaggregation['code2']))
                    }

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

                if existing_disaggregation is not None:
                    disagg_value = value_row['Value']
                    if not pd.isna(existing_disaggregation_dict['dimension1']):
                        if disagg_value in existing_disaggregation_dict['dimension1']:
                            dimension1 = existing_disaggregation_dict['dimension1'][disagg_value]
                            code1 = existing_disaggregation_dict['code1'][disagg_value]
                            dimension2 = existing_disaggregation_dict['dimension2'][disagg_value]
                            code2 = existing_disaggregation_dict['code2'][disagg_value]

                            if not pd.isna(dimension1):
                                disaggregation_sheet.write(dimension_1_cell, dimension1)
                            if not pd.isna(code1):
                                disaggregation_sheet.write(code_1_cell, code1)
                            if not pd.isna(dimension2):
                                disaggregation_sheet.write(dimension_2_cell, dimension2)
                            if not pd.isna(code2):
                                disaggregation_sheet.write(code_2_cell, code2)

                row += 1
            disaggregation_sheet.set_column('A:Z', 30)
            disaggregation_sheet.set_row(1, 20, header_format)

        workbook.close()


    def get_disaggregation_sheet_name(self, sheet_name):
        slug = slugify(sheet_name)
        if len(slug) > 24:
            slug = slug[0:24]
        while slug in self.sheet_names:
            slug = slug + '_'
        self.sheet_names.append(slug)
        return slug


    def create_dsd_from_map(self, dsd_path='dsd.xml', agency='Agency', version='1.0.0'):
        global_dsd = 'https://registry.sdmx.org/ws/public/sdmxapi/rest/datastructure/IAEG-SDGs/SDG/latest/?format=sdmx-2.1&detail=full&references=all&prettyPrint=true'

        urlretrieve(global_dsd, dsd_path)

        namespaces = dict([node for _, node in ET.iterparse(dsd_path, events=['start-ns'])])
        for ns in namespaces:
            ET.register_namespace(ns, namespaces[ns])
        tree = ET.parse(dsd_path)
        root = tree.getroot()

        dimensions = [
            'FREQ',
            'REPORTING_TYPE',
            'SERIES',
            'REF_AREA',
            'SEX',
            'AGE',
            'URBANISATION',
            'INCOME_WEALTH_QUANTILE',
            'EDUCATION_LEV',
            'OCCUPATION',
            'CUST_BREAKDOWN',
            'COMPOSITE_BREAKDOWN',
            'DISABILITY_STATUS',
            'ACTIVITY',
            'PRODUCT',
        ]

        codelist_mappings = self.parse_code_sheet()
        made_edits = False

        for dimension in dimensions:
            dimension_node = root.find('.//str:Dimension[@id="' + dimension + '"]', namespaces)
            codelist_id = dimension_node.find('./str:LocalRepresentation/str:Enumeration/Ref', namespaces).attrib['id']
            codelist_node = root.find('.//str:Codelist[@id="' + codelist_id + '"]', namespaces)
            codelist_urn = codelist_node.attrib['urn']
            custom_codes = codelist_mappings[[dimension, dimension + ' Name']].dropna()
            global_codes = [code.attrib['id'] for code in codelist_node.findall('.//str:Code', namespaces)]
            custom_codes = custom_codes[~custom_codes[dimension].isin(global_codes)]
            if custom_codes.empty:
                continue
            made_edits = True
            codelist_node.attrib['agencyID'] = agency
            for index, row in custom_codes.iterrows():
                custom_code = row[dimension]
                custom_name = row[dimension + ' Name']
                code_node = ET.SubElement(codelist_node, 'str:Code')
                code_node.attrib['id'] = custom_code
                code_node.attrib['urn'] = codelist_urn + '.' + custom_code
                code_name_node = ET.SubElement(code_node, 'com:Name')
                code_desc_node = ET.SubElement(code_node, 'com:Description')
                code_name_node.text = custom_name
                code_desc_node.text = custom_name
                code_name_node.attrib['xml:lang'] = 'en'
                code_desc_node.attrib['xml:lang'] = 'en'


        if made_edits:
            header_node = root.find('.//mes:Header', namespaces)

        tree.write(dsd_path)


    def read_mapping(self, map_path):
        return pd.read_excel(map_path,
            sheet_name=None,
            index_col=None,
            header=None,
            keep_default_na=False,
            na_values=['#REF!', '']
        )


    def parse_code_sheet(self):
        sheets = self.existing_map
        df = sheets['CODES']
        renamed_columns = []
        columns = df.iloc[1]
        last_column = None
        for column in columns:
            if column == 'Name':
                column = last_column + ' ' + 'Name'
            renamed_columns.append(column)
            last_column = column

        df.columns = renamed_columns
        df = df[2:]
        return df


    def parse_unit_sheet(self):
        sheets = self.existing_map
        df = sheets['UNITS']
        df = df[[3, 4]]
        df.columns = ['from', 'to']
        df = df.iloc[2:]
        return df.dropna()


    def parse_disaggregation_sheet(self, sheet_name):
        if sheet_name in self.existing_map:
            df = self.existing_map[sheet_name]

            first_na = 1000
            for index, row in df.iterrows():
                if pd.isna(row[0]):
                    first_na = index
                    break

            df = df.iloc[2:first_na]

            num_lang = len(self.disaggregation_report_service.languages)
            df = df[[0, num_lang, num_lang + 1, num_lang + 2, num_lang + 3]]
            df.columns = ['value', 'dimension1', 'code1', 'dimension2', 'code2']
            return df
        else:
            return None
