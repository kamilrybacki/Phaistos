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
    discover: bool
    logger: typing.ClassVar[logging.Logger] = MANAGER_LOGGER

    _current_schemas_path: typing.ClassVar[str] = ''
    _schemas: dict[str, SchemaInstancesFactory] = {}

    _started: typing.ClassVar[bool] = False
    __instance: typing.ClassVar[Manager | None] = None

    def validate(self, data: dict, schema: str) -> ValidationResults:
        self.logger.info(f'Validating data against schema: {schema}')
        return self.get_factory(schema).validate(data)

    @classmethod
    def start(
        cls,
        discover: bool = True,
        schemas_path: str | None = None
    ) -> Manager:
        cls._current_schemas_path = schemas_path or os.environ['PHAISTOS__SCHEMA_PATH']  # type: ignore
        if not cls._started:
            cls.logger.info('Starting Phaistos manager!')
            cls._started = True
            if 'PHAISTOS__DISABLE_SCHEMA_DISCOVERY' in os.environ:
                discover = False
            cls.__instance = cls(discover)
        return cls.__instance  # type: ignore

    @classmethod
    def _purge(cls) -> None:
        cls.__instance = None
        cls._started = False
        cls._current_schemas_path = ''
        cls._schemas = {}

    def __init__(self, discover: bool) -> None:
        if not self._started:
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

    def get_available_schemas(self) -> dict[str, SchemaInstancesFactory]:
        discovered_schemas = getattr(self, '_schemas', {})
        try:
            for schema in self.__discover_schemas(self._current_schemas_path):
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
