"""
This output assumes the following:
1. A DSD is already created and available
2. All columns in the data correspond exactly
   to dimension IDs.
3. All values in the columns correspond exactly
   to codes in those dimensions' codelists.
"""

import os
import sdg
import pandas as pd
import numpy as np
import sdmx
from datetime import datetime
from sdmx.model import (
    SeriesKey,
    Key,
    AttributeValue,
    Observation,
    GenericTimeSeriesDataSet,
    DataflowDefinition,
    Agency
)
from sdmx.message import (
    DataMessage,
    Header
)
from urllib.request import urlretrieve
from sdg.outputs import OutputBase

class OutputSdmxMl(OutputBase):
    """Output SDG data/metadata in SDMX-ML."""


    def __init__(self, inputs, schema, output_folder='_site', translations=None,
                 indicator_options=None, dsd='https://unstats.un.org/sdgs/files/SDG_DSD.xml',
                 default_values=None, message_id=''):
        """Constructor for OutputSdmxMl.

        Parameters
        ----------

        Inherits all the parameters from OutputBase, plus the following optional
        arguments (see above for the default values):

        dsd : string
            Remote URL of the SDMX DSD (data structure definition) or path to
            local file.
        default_values : dict
            Since SDMX output is required to have a value for every dimension/attribute
            you may need to specify defaults here. If not specified here, defaults for
            attributes will be '' and defaults for dimensions will be '_T'.
        message_id : string
            Optional identifying string to put in the "Sender" value in the header
            of the XML. This id will be followed by a timestamp to ensure uniqueness.
        """
        OutputBase.__init__(self, inputs, schema, output_folder, translations, indicator_options)
        self.message_id = message_id
        self.retrieve_dsd(dsd)
        sdmx_folder = os.path.join(output_folder, 'sdmx')
        if not os.path.exists(sdmx_folder):
            os.makedirs(sdmx_folder, exist_ok=True)
        self.sdmx_folder = sdmx_folder
        self.default_values = {} if default_values is None else default_values


    def retrieve_dsd(self, dsd):
        if dsd.startswith('http'):
            urlretrieve(dsd, 'SDG_DSD.xml')
            dsd = 'SDG_DSD.xml'
        msg = sdmx.read_sdmx(dsd)
        dsd_object = msg.structure[0]
        self.dsd = dsd_object


    def build(self, language=None):
        """Write the SDMX output. Overrides parent."""
        status = True
        datasets = []
        dfd = DataflowDefinition(id="OPEN_SDG_DFD", structure=self.dsd)

        # SDMX output is language-agnostic. Only the DSD contains language info.
        if language is not None:
            language = None

        for indicator_id in self.get_indicator_ids():
            indicator = self.get_indicator_by_id(indicator_id).language(language)
            data = indicator.data.copy()

            # Some hardcoded dataframe changes.
            data = data.rename(columns={
                'Value': 'OBS_VALUE',
                'Units': 'UNIT_MEASURE',
                'Series': 'SERIES',
                'Year': 'TIME_DETAIL',
            })
            data = data.replace(np.nan, '', regex=True)
            if data.empty:
                continue

            serieses = {}
            for _, row in data.iterrows():
                series_key = self.dsd.make_key(SeriesKey, self.get_dimension_values(row, indicator))
                series_key.attrib = self.get_series_attribute_values(row, indicator)
                attributes = self.get_observation_attribute_values(row, indicator)
                dimension_key = self.dsd.make_key(Key, values={
                    'TIME_PERIOD': str(row['TIME_DETAIL']),
                })
                observation = Observation(
                    series_key=series_key,
                    dimension=dimension_key,
                    attached_attribute=attributes,
                    value_for=self.dsd.measures[0],
                    value=row[self.dsd.measures[0].id],
                )
                if series_key not in serieses:
                    serieses[series_key] = []
                serieses[series_key].append(observation)

            dataset = GenericTimeSeriesDataSet(structured_by=self.dsd, series=serieses)
            header = self.create_header()
            time_period = next(dim for dim in self.dsd.dimensions if dim.id == 'TIME_PERIOD')
            msg = DataMessage(data=[dataset], dataflow=dfd, header=header, observation_dimension=time_period)
            sdmx_path = os.path.join(self.sdmx_folder, indicator_id + '.xml')
            with open(sdmx_path, 'wb') as f:
                status = status & f.write(sdmx.to_xml(msg))
            datasets.append(dataset)

        msg = DataMessage(data=datasets, dataflow=dfd)
        all_sdmx_path = os.path.join(self.sdmx_folder, 'all.xml')
        with open(all_sdmx_path, 'wb') as f:
            status = status & f.write(sdmx.to_xml(msg))

        return status


    def create_header(self):
        current_time = datetime.now()
        return Header(
            id='IREF' + self.message_id + str(current_time.timestamp()),
            test=True,
            prepared=current_time.strftime('%Y-%m-%dT%H:%M:%S'),
            sender=Agency(id='open-sdg/sdg-build@' + sdg.__version__),
        )


    def get_dimension_values(self, row, indicator):
        values = {}
        for dimension in self.dsd.dimensions:
            # Skip the TIME_PERIOD dimension because it is used as the "observation dimension".
            if dimension.id == 'TIME_PERIOD':
                continue
            value = row[dimension.id] if dimension.id in row else self.get_dimension_default(dimension.id, indicator)
            if value != '':
                values[dimension.id] = value
        return values


    def get_observation_attribute_values(self, row, indicator):
        return self.get_attribute_values(row, indicator, sdmx.model.PrimaryMeasureRelationship)


    def get_series_attribute_values(self, row, indicator):
        return self.get_attribute_values(row, indicator, sdmx.model.DimensionRelationship)


    def get_attribute_values(self, row, indicator, related_to):
        values = {}
        for attribute in self.dsd.attributes:
            if attribute.related_to is not None and isinstance(attribute.related_to, related_to):
                value = row[attribute.id] if attribute.id in row else self.get_attribute_default(attribute.id, indicator)
                if value != '':
                    values[attribute.id] = AttributeValue(value_for=attribute, value=value)
        return values


    def get_default_values(self):
        return self.default_values


    def get_dimension_default(self, dimension, indicator):
        indicator_value = indicator.get_meta_field_value(dimension)
        if indicator_value is not None:
            return indicator_value
        defaults = self.get_default_values()
        if dimension not in defaults:
            defaults = {
                'FREQ': 'A',
                'REPORTING_TYPE': 'N'
            }
        if dimension in defaults:
            return defaults[dimension]
        else:
            return '_T'


    def get_attribute_default(self, attribute, indicator):
        indicator_value = indicator.get_meta_field_value(attribute)
        if indicator_value is not None:
            return indicator_value
        defaults = self.get_default_values()
        if attribute in defaults:
            return defaults[attribute]
        else:
            return ''


    def get_documentation_title(self):
        return 'SDMX output'


    def get_documentation_content(self, languages=None, baseurl=''):

        indicator_ids = self.get_documentation_indicator_ids()

        endpoint = 'sdmx/{indicator_id}.xml'
        output = '<p>' + self.get_documentation_description() + ' Examples are below:<p>'
        output += '<ul>'
        path = endpoint.format(indicator_id='all')
        output += '<li><a href="' + path + '">' + path + '</a></li>'
        for indicator_id in indicator_ids:
            path = endpoint.format(indicator_id=indicator_id)
            output += '<li><a href="' + baseurl + path + '">' + path + '</a></li>'
        output += '<li>etc...</li>'
        output += '</ul>'

        return output


    def get_documentation_description(self):
        description = (
            "This output has an SDMX file for each indicator's data, "
            "plus one SDMX file with all indicator data. This data uses "
            "numbers and codes only, so is not specific to any language."
        )
        return description


    def validate(self):
        """Validate the data for the indicators."""

        # Need to figure out SDMX validation.
        return True
