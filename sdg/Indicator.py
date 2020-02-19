import copy
import json
import sdg
import pandas as pd
from sdg.translations import TranslationHelper

class Indicator:
    """Data model for SDG indicators."""

    def __init__(self, inid, name=None, data=None, meta=None):
        """Constructor for the SDG indicator instances.

        Parameters
        ----------
        inid : string
            The three-part dash-delimited ID (eg, 1-1-1).
        name : string
            The name of the indicator.
        data : Dataframe
            Dataframe of all data, with at least "Year" and "Value" columns.
        meta : dict
            Dict of fielded metadata.
        """
        self.inid = inid
        self.name = name
        self.data = data
        self.meta = meta
        self.set_headline()
        self.set_edges()
        self.translations = {}


    def has_name(self):
        """Check to see if the indicator has a name.

        Returns
        -------
        boolean
            True if the indicator has a name.
        """
        return self.name is not None


    def get_name(self):
        """Get the name of the indicator if known, or otherwise the id.

        Returns
        -------
        string
            The name (or id) of the indicator.
        """
        return self.name if self.name is not None else self.inid


    def set_name(self, name=None):
        """Set the name of the indicator."""
        if name is not None:
            self.name = name


    def has_data(self):
        """Check to see if this indicator has data.

        Returns
        -------
        boolean
            True if the indicator has data.
        """
        if self.data is None:
            # If data has not been set yet, return False.
            return False
        # Otherwise return False if there are no rows in the dataframe.
        return False if len(self.data) < 1 else True


    def has_meta(self):
        """Check to see if this indicator has metadata.

        Returns
        -------
        boolean
            True if the indicator has metadata.
        """
        return False if self.meta is None else True


    def set_data(self, val):
        """Set the indicator data if a value is passed.

        Parameters
        ----------
        val : Dataframe or None
        """
        # If empty or None, do nothing.
        if val is None or not isinstance(val, pd.DataFrame) or val.empty:
            return

        self.data = val
        self.set_headline()
        self.set_edges()


    def set_meta(self, val):
        """Set the indicator metadata if a value is passed.

        Parameters
        ----------
        val : Dict or None
        """
        if val is not None and val:
            if self.has_meta():
                self.meta.update(val)
            else:
                self.meta = val


    def set_headline(self):
        """Calculate and set the headline for this indicator."""
        self.require_data()
        self.headline = sdg.data.filter_headline(self.data)


    def set_edges(self):
        """Calculate and set the edges for this indicator."""
        self.require_data()
        self.edges = sdg.edges.edge_detection(self.inid, self.data)


    def get_goal_id(self):
        """Get the goal number for this indicator.

        Returns
        -------
        string
            The number of the goal.
        """
        return self.inid.split('-')[0]


    def get_target_id(self):
        """Get the target id for this indicator.

        Returns
        -------
        string
            The target id, dot-delimited.
        """
        return '.'.join(self.inid.split('-')[0:2])


    def get_indicator_id(self):
        """Get the indicator id for this indicator (dot-delimited version).

        Returns
        -------
        string
            The indicator id, dot-delimited.
        """
        return self.inid.replace('-', '.')


    def require_meta(self, minimum_metadata=None):
        """Ensure the metadata for this indicator has minimum necessary values.

        Parameters
        ----------
        minimum_metadata : Dict
            Key/value pairs of minimum metadata for this indicator.
        """
        if minimum_metadata is None:
            minimum_metadata = {}

        if self.meta is None:
            self.meta = minimum_metadata
        else:
            for key in minimum_metadata:
                if key not in self.meta:
                    self.meta[key] = minimum_metadata[key]


    def require_data(self):
        """Ensure at least an empty dataset for this indicator."""
        if self.data is None:
            df = pd.DataFrame({'Year':[], 'Value':[]})
            # Enforce the order of columns.
            cols = ['Year', 'Value']
            df = df[cols]
            self.data = df


    def language(self, language=None):
        """Return a translated copy of this indicator.

        Requires that the translate() method be run first.
        """
        if language is None:
            return self
        if language in self.translations:
            return self.translations[language]
        raise ValueError('Language ' + language + ' has not been translated.')


    def translate(self, language, translation_helper):
        """Translate the entire indicator into a particular language.

        Parameters
        ----------
        language : string
            The language code to translate into.
        translation_helper : TranslationHelper
            The instance of TranslationHelper to perform the translations.
        """
        # Already done? Abort now.
        if language in self.translations:
            return

        # Start with an empty indicator.
        indicator = Indicator(inid=self.inid)

        # Translation callbacks for below.
        def translate_meta(text):
            return translation_helper.translate(text, language)
        def translate_data(text):
            return translation_helper.translate(text, language, default_group='data')

        # Translate the name.
        indicator.set_name(translate_meta(self.name))

        # Translate the metadata.
        meta_copy = copy.deepcopy(self.meta)
        for key in meta_copy:
            meta_copy[key] = translate_meta(meta_copy[key])
        indicator.set_meta(meta_copy)

        # Translate the data cells and headers.
        data_copy = copy.deepcopy(self.data)
        for column in data_copy:
            data_copy[column] = data_copy[column].apply(translate_data)
        data_copy.rename(mapper=translate_data, axis='columns', inplace=True)
        indicator.set_data(data_copy)

        # Finally place the translation for later access.
        self.translations[language] = indicator


    def is_complete(self):
        """Decide whether this indicator can be considered "complete".

        Returns
        -------
        boolean
            True if the indicator can be considered "complete", False otherwise.
        """
        # First, check for an open-sdg-style "reporting_status" metadata field,
        # for a value of "complete".
        reporting_status = self.get_meta_field_value('reporting_status')
        if reporting_status is not None and reporting_status == 'complete':
            return True
        # If there was some other reporting status, assume not complete.
        elif reporting_status is not None:
            return False
        # Otherwise fall back to whether the indicator has data and metadata.
        else:
            return self.has_data() and self.has_meta()


    def is_statistical(self):
        """Decide whether this indicator can be considered "statistical".

        Returns
        -------
        boolean
            True if the indicator can be considered statistical, False otherwise.
        """
        # First, check for an open-sdg-style "data_non_statistical" metadata field.
        non_statistical = self.get_meta_field_value('data_non_statistical')
        if non_statistical is None or non_statistical == False:
            return True
        # If the the indicator was explicitly non-statistical, return False.
        elif non_statistical == True:
            return False
        # Otherwise fall back to whether the indicator has data.
        else:
            return self.has_data()


    def get_meta_field_value(self, field):
        """Get the value for a metadata field.

        Parameters
        ----------
        field : string
            The key of the metadata field.

        Return : string or None
            The value of the specified field or just None if the field could not
            be found.
        """

        if not self.has_meta():
            return None

        if field not in self.meta:
            return None

        return self.meta[field]


    def get_all_series(self):
        """Indicator data can have multiple combinations of disaggregations,
        which are here called "series". For our purposes, a "series" is a full
        set of available years (for example, 2008, 2009, and 2010) with the
        corresponding values (for example, 0.7, 0.8, and 0.9) and a description
        of how it is disaggregated (for example, Female, Age 60+, Urban).

        Each series is a dict containing a 'disaggregations' dict and a 'values'
        dict. For example:

        {
            'disaggregations': {
                'Sex': 'Female',
                'Age': '60+',
                'Area': 'Urban'
            },
            'values': {
                2008: 0.7,
                2009: 0.8,
                2010: 0.9
            }
        }
        """
        all_series = {}
        for index, row in self.data.iterrows():
            # Assume "disaggregations" are everything except 'Year' and 'Value'.
            disaggregations = row.drop('Value').drop('Year').to_dict()
            # Serialize so that we can use a set of disaggregations as a key.
            serialized = json.dumps(disaggregations, sort_keys=True)
            # Initialized any new series.
            if serialized not in all_series:
                all_series[serialized] = sdg.Series(disaggregations)
            # Finally add the year and value.
            all_series[serialized].add_value(row['Year'], row['Value'])

        # We only want to return a list, not a dict.
        return all_series.values()
