import os
from sdg.json import write
from sdg.outputs import OutputBase
from sdg.stats import reporting_status

class OutputReportingStatus(OutputBase):
    """Output SDG reporting statistics."""


    def execute(self):
        """Write JSON output with statistics about SDG reporting status."""
        all_meta = dict()

        for inid in self.indicators:
            all_meta[inid] = self.indicators[inid].meta

        status_json = reporting_status(self.schema, all_meta)

        return write(status_json, 'reporting.json', self.output_folder)
