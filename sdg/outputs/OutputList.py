class OutputList:
    """A list of OutputBase descendants."""


    def __init__(self, outputs):
        """Constructor for the OutputList class.

        Parameters
        ----------
        outputs : list
            Required list of objects inheriting from OutputBase.
        """
        self.__outputs = outputs


    def get_all_indicators(self):
        """Get a combined dict of all the indicators across all outputs.

        The dict is keyed by indicator ID to ensure there are no duplicates.
        
        Returns
        -------
        dict
            Indicator objects keyed by indicator ID.
        """
        indicators = {}
        for output in self.get_outputs():
            for indicator_id in output.get_indicator_ids():
                indicators[indicator_id] = output.get_indicator_by_id(indicator_id)
        return indicators
    

    def get_outputs(self):
        return self.__outputs
