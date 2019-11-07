import copy
import os
from sdg.translations import TranslationInputBase
from sdg.translations import TranslationHelper

class OutputBase:
    """Base class for destinations of SDG data/metadata."""


    def __init__(self, inputs, schema, output_folder='', translations=[]):
        """Constructor for OutputBase."""
        self.indicators = self.merge_inputs(inputs)
        self.schema = schema
        self.output_folder = output_folder
        self.translations = translations
        # Safety code to ensure translations are a list of inputs.
        if isinstance(self.translations, TranslationInputBase):
            self.translations = [translations]
        # Create a translation helper.
        self.translation_helper = TranslationHelper(self.translations)


    def execute():
        """Write the SDG output to disk."""
        raise NotImplementedError


    def merge_inputs(self, inputs):
        """Take the results of many inputs and merge into a single dict of indicators."""
        merged_indicators = {}
        for input in inputs:
            # Fetch the input.
            input.execute()
            # Merge the results.
            for inid in input.indicators:
                if inid not in merged_indicators:
                    # If this indicator is new, simply use it.
                    merged_indicators[inid] = input.indicators[inid]
                else:
                    # Otherwise if this indicator was already there, it needs to
                    # be "merged" in. To do this, we manually set data, metadata,
                    # and name. Note that all of these "set" methods abort if
                    # the value is None, so we don't need to check for None here.
                    merged_indicators[inid].set_data(input.indicators[inid].data)
                    merged_indicators[inid].set_meta(input.indicators[inid].meta)
                    merged_indicators[inid].set_name(input.indicators[inid].name)

        for inid in merged_indicators:
            # Now that everything has been merged, we have to make sure that
            # minimum data and metadata is set.
            merged_indicators[inid].require_data()
            merged_indicators[inid].require_meta(self.minimum_metadata(merged_indicators[inid]))
            # And because this may affect data, we have to re-do headlines and
            # edges.
            merged_indicators[inid].set_headline()
            merged_indicators[inid].set_edges()

        return merged_indicators


    def validate(self):
        """Validate the data and metadata for the indicators."""

        status = True
        for inid in self.indicators:
            status = status & self.schema.validate(self.indicators[inid])

        return status


    def backup_indicators(self):
        """Store a backup version of the indicators."""
        if hasattr(self, 'originals'):
            # We've already done this, abort.
            return

        self.originals = {}
        for inid in self.indicators:
            self.originals[inid] = copy.deepcopy(self.indicators[inid])


    def execute_per_language(self, languages):
        """This triggers calls to execute() for each language - once each."""
        # Make sure we keep a copy of the originals before doing any translations.
        original_indicators = {}
        for inid in self.indicators:
            original_indicators[inid] = copy.deepcopy(self.indicators[inid])
        # Also keep a backup of the output folder.
        original_output_folder = self.output_folder
        # Now loop through each language.
        for language in languages:
            # Temporarily change the output folder.
            self.output_folder = os.path.join(original_output_folder, language)
            # And within each language, each indicator.
            for inid in self.indicators:
                # Start with the original.
                self.indicators[inid] = copy.deepcopy(original_indicators[inid])
                # Translate it.
                self.indicators[inid].translate(language, self.translation_helper)
            # Now perform the build.
            self.execute()

        # Cleanup afterwards.
        self.indicators = original_indicators
        self.output_folder = original_output_folder


    def minimum_metadata(self, indicator):
        """Each subclass can specify it's own minimum viable metadata values.

        Parameters
        ----------
        indicator : Indicator
            The indicator instance to set minimum metadata for

        Returns
        -------
        dict
            Key/value pairs for minimum required metadata
        """
        return {}
