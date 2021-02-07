import pandas as pd
import sdg
from sdg.inputs import InputFiles
from sdg.Indicator import Indicator

class InputCsvData(InputFiles):
    """Sources of SDG data that are local CSV files."""

    def convert_filename_to_indicator_id(self, filename):
        if self.indicator_id_pattern is not None:
            return InputFiles.convert_filename_to_indicator_id(self, filename)
        else:
            return filename.replace('indicator_', '')


    def execute(self, indicator_options):
        """Get the data, edges, and headline from CSV, returning a list of indicators."""
        indicator_map = self.get_indicator_map()
        for inid in indicator_map:
            data = pd.read_csv(indicator_map[inid])
            self.add_indicator(inid, data=data, options=indicator_options)
