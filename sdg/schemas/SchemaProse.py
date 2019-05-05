# -*- coding: utf-8 -*-

import yaml
import json
import os
from sdg.json import write_json
from sdg.schemas import SchemaBase


class SchemaProse(SchemaBase):
    """
    The SchemaProse class loads in everything we know about the metadata from
    a schema file intended for Prose.io.
    """


    def __init__(self, schema_path='_prose.yml'):
        """Create a new SchemaProse object

        Args:
            schema_path: Path to the schema file, such as '_prose.yml'.
        """

        self.schema_path = schema_path
        SchemaBase.__init__(self)


    def load_schema(self):
        """Load a schema according to this instance's properties."""

        with open(self.schema_path, encoding="UTF-8") as stream:
            config = next(yaml.safe_load_all(stream))

        schema = dict()
        for field in config['prose']['metadata']['meta']:
            schema[field['name']] = field['field']

        self.schema = schema
