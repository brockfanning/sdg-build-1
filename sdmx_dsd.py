import os
import sdg

# Input data from CSV files matching this pattern: tests/data/*-*.csv
data_pattern = os.path.join('tests', 'data', '*-*.csv')
data_input = sdg.inputs.InputCsvData(path_pattern=data_pattern)

inputs = [data_input]

dsd_path = os.path.join('tests', 'sdmx', 'dsd.xml')
map_folder_path = os.path.join('tests', 'sdmx', 'map_files')

sdmx_dsd_service = sdg.SdmxDsdService(inputs, map_folder_path, dsd_path)
