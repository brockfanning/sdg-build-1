import os
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from io import StringIO

class SdmxDsdService():
    """Read and parse an SDMX DSD."""

    def __init__(self, dsd_path='https://registry.sdmx.org/ws/public/sdmxapi/rest/datastructure/IAEG-SDGs/SDG/latest/?format=sdmx-2.1&detail=full&references=all&prettyPrint=true'):
        """Constructor for SdmxDsdService.

        Parameters
        ----------
        dsd_path : string
            Optional path to local or remote DSD. Defaults to the global DSD.
        """
        self.dsd = self.__parse_xml(dsd_path)


    def __parse_xml(self, location, strip_namespaces=True):
        """Fetch and parse an XML file.

        Parameters
        ----------
        location : string
            Remote URL of the XML file or path to local file.
        strip_namespaces : boolean
            Whether or not to strip namespaces. This is helpful in cases where
            different implementations may use different namespaces/prefixes.
        """
        xml = self.__fetch_file(location)
        it = ET.iterparse(StringIO(xml))
        if strip_namespaces:
            for _, el in it:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]
        return it.root


    def __fetch_file(self, location):
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


    def get_dimension_code_pairs(self):
        pairs = []
        for dimension in self.get_dimension_ids():
            codes = self.get_code_ids_by_dimension(dimension)
            dimension_code_pairs = [(dimension, code) for code in codes]
            pairs.extend(dimension_code_pairs)
        return pairs


    def get_dimension_ids(self):
        xpath = ".//DimensionList/Dimension"
        matches = self.dsd.findall(xpath)
        return [match.attrib['id'] for match in matches]


    def get_code_ids_by_dimension(self, dimension_id):
        xpath = ".//DimensionList/Dimension[@id='{}']"
        dimension = self.dsd.find(xpath.format(dimension_id))
        if dimension is None:
            return []
        ref = dimension.find(".//Ref[@package='codelist']")
        codelist_id = ref.attrib['id']
        xpath = ".//Codelists/Codelist[@id='{}']/Code"
        matches = self.dsd.findall(xpath.format(codelist_id))
        return [match.attrib['id'] for match in matches]
