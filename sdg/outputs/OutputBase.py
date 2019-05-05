import os

class OutputBase:
    """Base class for destinations of SDG data/metadata."""

    def __init__(self, inputs, schema, output_folder=''):
        """Constructor for OutputBase."""
        self.indicators = self.merge_inputs(inputs)
        self.schema = schema
        self.output_folder = output_folder

        # Make sure the output folder exists.
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

    def execute():
        """Write the SDG output to disk.

        All subclasses must override this method.
        """
        raise NotImplementedError

    def merge_inputs(self, inputs):
        """Take the results of many inputs and merge into a single dict of indicators.

        Args:
            inputs -- list: A list of InputBase (subclassed) objects

        Return:
            merged_indicators -- dict: Indicator objects keyed by indicator id
        """
        merged_indicators = {}
        for input in inputs:
            # Fetch the input.
            input.execute()
            # Merge the results.
            for inid in input.indicators:
                if inid not in merged_indicators:
                    merged_indicators[inid] = input.indicators[inid]
                else:
                    merged_indicators[inid].set_data(input.indicators[inid].data)
                    merged_indicators[inid].set_meta(input.indicators[inid].meta)

        return merged_indicators
