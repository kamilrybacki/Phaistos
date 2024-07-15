from __future__ import annotations
import logging
import os
import typing
import yaml


from phaistos.transpiler import Transpiler
from phaistos.typings import (
    SchemaInputFile,
    ValidationResults
)
from phaistos.schema import TranspiledSchema, SchemaInstancesFactory
from phaistos.consts import DISCOVERY_EXCEPTIONS, MANAGER_LOGGER
from phaistos.exceptions import SchemaLoadingException


class Manager:
    discover: bool = True
    _schemas: dict[str, SchemaInstancesFactory] = {}
    logger: typing.ClassVar[logging.Logger] = MANAGER_LOGGER

    __instance: typing.ClassVar[Manager | None] = None
    __started: typing.ClassVar[bool] = False
    __last_used_schemas_dir: typing.ClassVar[str] = ''

    def validate(self, data: dict, schema: str) -> ValidationResults:
        self.logger.info(f'Validating data against schema: {schema}')
        return self.get_factory(schema).validate(data)

    @classmethod
    def start(
        cls,
        discover: bool = bool(
            os.environ.get('PHAISTOS__DISABLE_SCHEMA_DISCOVERY')
        )
    ) -> Manager:
        if cls.__started and cls.__last_used_schemas_dir != os.environ.get('PHAISTOS__SCHEMA_PATH', ''):
            cls.logger.info('Schema path has changed. Reloading schemas.')
            cls.__instance = None
            cls.__started = False
        if not cls.__instance:
            cls.logger.info('Starting Phaistos manager!')
            cls.__started = True
            cls.__last_used_schemas_dir = os.environ.get('PHAISTOS__SCHEMA_PATH', '')
            cls.__instance = cls(discover)
        return cls.__instance

    def __init__(self, discover: bool) -> None:
        if not self.__started:
            raise RuntimeError(
                'Validator must be started using Manager.start()'
            )
        if discover:
            self._schemas = self.get_available_schemas()

    def get_factory(self, name: str) -> SchemaInstancesFactory:
        """
        Get a schema factory by name

        Args:
            name (str): The name of the schema

        Returns:
            SchemaInstancesFactory: The schema factory, that can be used to validate data and create instances of the model
        """
        if name not in self._schemas:
            raise SchemaLoadingException(
                f'Schema {name} not found'
            )
        return self._schemas[name]

    def get_available_schemas(self, path: str = '') -> dict[str, SchemaInstancesFactory]:
        discovered_schemas = getattr(self, '_schemas', {})
        try:
            schemas_dir = path or os.environ['PHAISTOS__SCHEMA_PATH']
            for schema in self.__discover_schemas(schemas_dir):
                discovered_schemas[schema.transpilation_name] = SchemaInstancesFactory(
                    name=schema.transpilation_name,
                    _model=schema
                )
        except tuple(DISCOVERY_EXCEPTIONS.keys()) as schema_discovery_error:
            self.logger.error(
                DISCOVERY_EXCEPTIONS.get(type(schema_discovery_error), f'Error while discovering schemas: {schema_discovery_error}')
            )
            raise schema_discovery_error

        self.logger.info(
            f'Available schemas: {", ".join(discovered_schemas.keys())}'
        )
        return discovered_schemas

    def __discover_schemas(self, target_path: str) -> list[type[TranspiledSchema]]:
        self.logger.info(f'Discovering schemas in: {target_path}')
        schemas: list[type[TranspiledSchema]] = []
        for schema in os.listdir(target_path):
            if schema.startswith('_'):
                continue

            schema_path = f'{target_path}/{schema}'
            if not os.path.isdir(schema_path):
                self.logger.info(f'Importing schema: {schema_path}')

                with open(schema_path, 'r', encoding='utf-8') as schema_file:
                    schema_data = yaml.safe_load(schema_file)
                    self.load_schema(schema_data)
                continue

            nested_schemas = self.__discover_schemas(schema_path)
            schemas.extend(nested_schemas)
        return schemas

    def load_schema(self, schema: SchemaInputFile) -> str:
        self.logger.info(f'Loading schema: {schema["name"]}')
        schema_class = Transpiler.make_schema(schema)
        self._schemas[schema['name']] = SchemaInstancesFactory(
            name=schema_class.transpilation_name,
            _model=schema_class
        )
        return schema_class.transpilation_name
