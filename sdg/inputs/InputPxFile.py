import pandas as pd
import sdg
from sdg.inputs import InputBase
from sdg.Indicator import Indicator
from sdg.helpers.px import Px
import re


class InputPxFile(InputBase):
    """Sources of SDG data that are local PX files."""

    def __init__(self,
        indicator_id_map=None,
        logging=None,
        column_map=None,
        code_map=None,
        request_params=None,
        meta_suffix=None
    ):
        """Constructor for InputPxFile.

        Keyword arguments:
        source: local or remote location of PX file.
        """
        InputBase.__init__(self,
            logging=logging,
            column_map=column_map,
            code_map=code_map,
            request_params=request_params,
            meta_suffix=meta_suffix
        )
        if indicator_id_map is None:
            indicator_id_map = {}                   
        self.indicator_id_map = indicator_id_map


    def execute(self, indicator_options):
        for indicator_id, source in self.indicator_id_map.items():
            pc_axis = self.fetch_file(source)
            px = Px(pc_axis)
            # Prepare the data.
            df = pd.DataFrame(px.entries())
            year_column = px.get_year_column_name()
            value_column = px.get_value_column_name()
            units_column = px.get_units_column_name()
            df.rename(inplace=True, columns = {
                year_column: 'Year',
                value_column: 'Value',
                units_column: indicator_options.get_unit_column(),
            })
            # Prepare the metadata.
            metadata = {}
            keywords = px.keywords()
            if 'UNITS' in keywords:
                metadata['computation_units'] = px.keyword('UNITS')
            if 'NOTE' in keywords:
                metadata['data_footnote'] = px.keyword('NOTE')
            if 'TITLE' in keywords:
                metadata['graph_title'] = px.keyword('TITLE')
                metadata['indicator_name'] = px.keyword('TITLE')
            # Add the indicator.
            self.add_indicator(indicator_id, data=df, meta=metadata, options=indicator_options)
            print(px.values('sex', 'fo'))
