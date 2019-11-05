# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
from xml.etree import ElementTree as ET
from io import StringIO
from sdg.translations import TranslationInputBase

class TranslationInputSdmx(TranslationInputBase):
    """A class for importing translations from an SDMX DSD."""


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
                for attrib in el.attrib:
                    if '}' in attrib:
                        val = el.attrib[attrib]
                        del el.attrib[attrib]
                        attrib = attrib.split('}', 1)[1]
                        el.attrib[attrib] = val

        return it.root


    def execute(self):
        dsd = self.parse_xml(self.source)
        groups = {
            'category': {
                'xpath': './/Category',
                'translations': './/Name'
            },
            'codelist': {
                'xpath': './/Codelist',
                'translations': './/Name'
            },
            'code': {
                'xpath': './/Code',
                'translations': './/Name'
            },
            'concept': {
                'xpath': './/Concept',
                'translations': './/Name'
            }
        }
        for group in groups:
            tags = dsd.findall(groups[group]['xpath'])
            for tag in tags:
                key = tag.attrib['id']
                translations = tag.findall(groups[group]['translations'])
                for translation in translations:
                    if 'lang' not in translation.attrib:
                        continue
                    language = translation.attrib['lang']
                    self.add_translation(language, group, key, translation.text)

        print(self.translations)

