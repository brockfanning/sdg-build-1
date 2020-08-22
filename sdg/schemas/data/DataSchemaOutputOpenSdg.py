# -*- coding: utf-8 -*-

import os
import json
from sdg.schemas.data import DataSchemaOutputBase

class DataSchemaOutputOpenSdg(DataSchemaOutputBase):
    """A class for outputing a data schema to the Open SDG JSON file."""


    def write_schema(self, output_folder='meta', filename='schema.json'):
        """Write the Open SDG schema file to disk. Overrides parent.

        Parameters
        ----------
        output_folder : string
            The folder to write the schema output in
        filename : string
            The filename for writing the schema output
        """

        # Make sure the folder exists.
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, filename)

        output = list()

        output_json = json.dumps(output)
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(output_json)
