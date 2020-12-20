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
                for at in list(el.attrib.keys()):
                    if '}' in at:
                        newat = at.split('}', 1)[1]
                        el.attrib[newat] = el.attrib[at]
                        del el.attrib[at]
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


    def get_dimension_ids(self):
        return [dimension.attrib['id'] for dimension in self.get_dimensions()]


    def get_dimensions(self):
        xpath = ".//DimensionList/Dimension"
        return self.dsd.findall(xpath)


    def get_dimension_by_id(self, dimension_id):
        xpath = ".//DimensionList/Dimension[@id='{}']"
        return self.dsd.find(xpath.format(dimension_id))


    def get_codes_by_dimension_id(self, dimension_id):
        dimension = self.get_dimension_by_id(dimension_id)
        if dimension is None:
            return []
        ref = dimension.find(".//Ref[@package='codelist']")
        codelist_id = ref.attrib['id']
        xpath = ".//Codelists/Codelist[@id='{}']/Code"
        return self.dsd.findall(xpath.format(codelist_id))


    def get_code_id(self, code):
        return code.attrib['id']


    def get_code_name(self, code, language=None):
        xpath = "./Name"
        if language is not None:
            xpath = "./Name[@lang='{}']".format(language)
        name = code.find(xpath)
        if name is not None:
            return name.text
        else:
            return ''


    def get_codes_by_attribute_id(self, attribute_id):
        attribute = self.get_attribute_by_id(attribute_id)
        if attribute is None:
            return []
        ref = attribute.find(".//Ref[@package='codelist']")
        codelist_id = ref.attrib['id']
        xpath = ".//Codelists/Codelist[@id='{}']/Code"
        return self.dsd.findall(xpath.format(codelist_id))


    def get_attribute_by_id(self, attribute_id):
        xpath = ".//AttributeList/Attribute[@id='{}']"
        return self.dsd.find(xpath.format(attribute_id))
