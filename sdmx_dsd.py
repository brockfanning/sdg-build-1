"""
This is an example of converting CSV data into GeoJSON output suitable for use
on a regional map.
"""

import os
import sdg

# Input data from CSV files matching this pattern: tests/data/*-*.csv
data_pattern = os.path.join('tests', 'data', '*-*.csv')
data_input = sdg.inputs.InputCsvData(path_pattern=data_pattern)

inputs = [data_input]

dsd_path = os.path.join('tests', 'sdmx', 'dsd.xml')
map_folder_path = os.path.join('tests', 'sdmx', 'map_files')

sdmx_dsd_service = sdg.SdmxDsdService(inputs, map_folder_path, dsd_path)
sdmx_dsd_service.update_files()

"""
# Validate the indicators.
validation_successful = geojson_output.validate()

# If everything was valid, perform the build.
if validation_successful:
    # Here are several ways you can generate the build:
    # 1. Translated into a single language, like English: geojson_output.execute('en')
    #    (the build will appear in '_site/en')
    # 2. Translated into several languages: geojson_output.execute_per_language(['es', 'ru', 'en'])
    #    (three builds will appear in '_site/es', '_site/ru', and '_site/en')
    # 3. Untranslated: geojson_output.execute()
    #    (the build will appear in '_site')
    geojson_output.execute_per_language(['es', 'ru', 'en'])
else:
    raise Exception('There were validation errors. See output above.')
"""
