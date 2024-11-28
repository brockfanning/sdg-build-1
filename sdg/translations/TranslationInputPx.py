# -*- coding: utf-8 -*-

import os
import shutil
import yaml
from sdg.translations import TranslationInputBase
from sdg.helpers.px import Px

class TranslationInputPx(TranslationInputBase):
    """This class imports translations from local or remote PX files."""

    def __init__(self, indicator_id_map=None, logging=None):
        """Constructor for the TranslationInputPx class.

        Parameters
        ----------
        indicator_id_map : dict
            A dict of indicator ids (dot-delimited) to PX file locations.
        """
        TranslationInputBase.__init__(self, logging=logging)
        if indicator_id_map is None:
            indicator_id_map = {}
        self.indicator_id_map = indicator_id_map

        #self.add_translation(language, group, key, value)



    def execute(self):
        TranslationInputBase.execute(self)
        for indicator_id, source in self.indicator_id_map.items():
            pc_axis = self.fetch_file(source)
            px = Px(pc_axis)
            default_language = px.get_default_language()
            languages = px.get_languages()
            if languages is None:
                continue
            variables = px.variables()
            translatable_variables = [v for v in variables if v != px.get_year_column_name()]
            for translatable_variable in translatable_variables:
                for language in languages:
                    suffix = ''
                    if language != default_language:
                        suffix = '[' + language + ']'
        