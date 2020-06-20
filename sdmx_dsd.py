import os
import sdg

# Input data from CSV files matching this pattern: tests/data/*-*.csv
data_pattern = os.path.join('tests', 'data', '*-*.csv')
data_input = sdg.inputs.InputCsvData(path_pattern=data_pattern)

meta_pattern = os.path.join('tests', 'meta', '*.md')
meta_input = sdg.inputs.InputYamlMdMeta(path_pattern=meta_pattern)

inputs = [data_input, meta_input]

translations = [
    sdg.translations.TranslationInputSdgTranslations(source='https://github.com/open-sdg/sdg-translations.git', tag='master'),
]

dsd_path = os.path.join('tests', 'sdmx', 'dsd.xml')
map_folder_path = os.path.join('tests', 'sdmx', 'map_files')

sdmx_dsd_service = sdg.SdmxDsdService(inputs, map_folder_path, dsd_path, translations=translations, country_code='KK')
sdmx_dsd_service.write_excel_maps()
