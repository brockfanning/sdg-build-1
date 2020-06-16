import os
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from io import StringIO
import pandas as pd
import sdg
from sdg.outputs import OutputBase

class SdmxDsdService(OutputBase):
    """Output an SDMX DSD and mapping files in CSV format.


    Takes as parameters:
        Path to a local DSD
        Path to an output folder
    If path to local DSD is provided, load it into memory
    Otherwise download and load the global DSD
    Get all disaggregations/values from data
    If mapping files exist in the output folder:
        Adds stuff to in-memory DSD as indicated by the mapping files
    If all disaggregations/values were mapped
        Write the local DSD to a temp file
        Compare it to existing local DSD.
        If any change, write it and bump the version
    Otherwise:
        Display a warning about the missing disaggregations/values
        Write missing disaggregations/values to the mapping files


    Notes:
        * Never removes mappings - only displays warnings about unused mappings
    """


    def __init__(self, inputs, map_folder_path, dsd_path, translations=None):
        """Constructor for SdmxDsdService.

        Parameters
        ----------

        inputs : list
            List of InputBase (or descendant) objects. Note - only data is
            needed (metadata is not used).
        map_folder_path : string
            Path to the folder with versioned CSV files for mapping SDMX codes
        dsd_path : string
            Path to a local (versioned) DSD
        translations : list
            List of TranslationInputBase (or descendant) classes

        """
        if translations is None:
            translations = []

        # This is not technically an "output", but it needs much the same as an
        # output, so it extends from OutputBase.
        OutputBase.__init__(self, inputs, None, None, translations)

        self.dsd_exists = os.path.exists(dsd_path)
        self.dsd_path = dsd_path
        self.map_folder_exists = os.path.exists(map_folder_path)
        self.map_folder_path = map_folder_path
        self.map = self.get_map()

        if not self.map_folder_exists:
            os.makedirs(self.map_folder_path, exist_ok=True)


    def update_files(self):
        if not self.dsd_exists:
            self.dsd = self.parse_xml('https://registry.sdmx.org/ws/public/sdmxapi/rest/datastructure/IAEG-SDGs/SDG/latest/?format=sdmx-2.1&detail=full&references=all&prettyPrint=true')
        else:
            self.dsd = self.parse_xml(self.dsd_path)

        #print(self.dsd_contains_codelist('CL_SERIES'))
        concepts_from_data = self.get_concepts_from_data()
        concepts_not_in_map = []
        for concept in concepts_from_data:
            if not self.concept_is_mapped(concept['CSV Column']):
                concepts_not_in_map.append(concept)

        if len(concepts_not_in_map) > 0:
            missing_concepts = self.get_dataframe_for_concepts(concepts_not_in_map)
            self.map = pd.concat([self.map, missing_concepts])
            self.write_map()


    def write_map(self):
        path = os.path.join(self.map_folder_path, 'concepts.csv')
        self.map.to_csv(path, index=False)


    def concept_is_mapped(self, column_name):
        return column_name in self.map['CSV Column']


    def parse_xml(self, location, strip_namespaces=True):
        """Fetch and parse an XML file.

        Parameters
        ----------
        location : string
            Remote URL of the XML file or path to local file.
        strip_namespaces : boolean
            Whether or not to strip namespaces. This is helpful in cases where
            different implementations may use different namespaces/prefixes.
        """
        xml = self.fetch_file(location)
        it = ET.iterparse(StringIO(xml))
        if strip_namespaces:
            for _, el in it:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]
        return it.root


    def fetch_file(self, location):
        """Fetch a file, either on disk, or on the Internet.

        Parameters
        ----------
        location : String
            Either an http address, or a path on disk
        """
        file = None
        data = None
        if location.startswith('http'):
            file = urlopen(location)
            data = file.read().decode('utf-8')
        else:
            file = open(location)
            data = file.read()
        file.close()
        return data


    def get_map(self):
        if not self.map_folder_exists:
            return self.get_dataframe_for_concepts()
        map_path = os.path.join(self.map_folder_path, 'concepts.csv')
        if not os.path.exists(map_path):
            return self.get_dataframe_for_concepts()
        return pd.read_csv(map_path)


    def get_code_mappings(self, codelist):
        if not self.map_folder_exists:
            return {}
        map_path = os.path.join(self.map_folder_path, codelist + '.csv')
        return pd.read_csv(map_path)


    def dsd_contains_codelist(self, codelist):
        xpath = ".//Codelist[@id='{}']"
        matches = self.dsd.findall(xpath.format(codelist))
        return len(matches) > 0


    def dsd_contains_code(self, codelist, code):
        # TODO
        pass


    def dsd_codelist_ids(self):
        xpath = ".//Codelist"
        matches = self.dsd.findall(xpath)
        return [match.attrib['id'] for match in matches]


    def dsd_dimension_ids(self):
        xpath = ".//DimensionList/Dimension"
        matches = self.dsd.findall(xpath)
        return [match.attrib['id'] for match in matches]


    def get_concepts_from_data(self):
        # Get all concepts in the data.
        concepts = {}
        for indicator_id in self.get_indicator_ids():
            indicator = self.get_indicator_by_id(indicator_id)
            columns = list(indicator.data.columns)
            for column in columns:
                if not self.is_column_a_concept_in_global_dsd(column):
                    concepts[column] = self.get_concept_from_column(column)
        return concepts.values()


    #def get_concept_from_dsd(self, concept_id):
    def get_concept_from_column(self, column_name):
        return {
            'CSV Column': column_name,
            'Concept Name': '',
            'Role': 'Dimension',
            'Type': 'Code',
            'Code List': '',
            'Code List Maintenance Agency': '',
            'Code List version': '',
            'Comment': ''
        }


    def get_dataframe_for_concepts(self, data=None):
        columns = self.get_concept_from_column('').keys()
        return pd.DataFrame(data=data, columns=columns)


    def is_column_a_concept_in_global_dsd(self, column_name):
        return column_name in [
            'Value',
            'Units',
            'Observation status',
            'Unit multiplier'
        ]
