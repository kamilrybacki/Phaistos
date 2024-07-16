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
    logger: typing.ClassVar[logging.Logger] = MANAGER_LOGGER

    _discover: bool
    _current_schemas_path: typing.ClassVar[str] = ''
    _schemas: dict[str, SchemaInstancesFactory] = {}
    _started: typing.ClassVar[bool] = False

    __instance: typing.Optional[Manager] = None

    def validate(self, data: dict, schema: str) -> ValidationResults:
        self.logger.info(f'Validating data against schema: {schema}')
        return self.get_factory(schema).validate(data)

    @classmethod
    def start(
        cls,
        discover: bool = True,
        schemas_path: str = ''
    ) -> Manager:
        cls._discover = discover
        if 'PHAISTOS__DISABLE_SCHEMA_DISCOVERY' in os.environ:
            cls._discover = False
        if not cls._started:
            cls._current_schemas_path = schemas_path or os.environ.get('PHAISTOS__SCHEMA_PATH', '')
            cls.__instance = cls()
        return cls.__instance  # type: ignore

    @classmethod
    def __new__(
        cls,
        *args,
        **kwargs
    ) -> Manager:
        if cls.__instance:
            return cls.__instance
        cls.logger.info('Starting Phaistos manager!')
        if not cls._current_schemas_path and cls._discover:
            raise RuntimeError(
                'Schemas path must be provided or PHAISTOS__SCHEMA_PATH environment variable must be set'
            )
        cls._started = True
        if cls._discover:
            cls.get_available_schemas()
        return super().__new__(cls)

    @classmethod
    def reset(cls) -> None:
        cls._started = False
        cls._current_schemas_path = ''
        cls._schemas = {}

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

    @classmethod
    def get_available_schemas(cls) -> dict[str, SchemaInstancesFactory]:
        discovered_schemas = getattr(cls, '_schemas', {})
        try:
            for schema in cls.__discover_schemas(cls._current_schemas_path):
                discovered_schemas[schema.transpilation_name] = SchemaInstancesFactory(
                    name=schema.transpilation_name,
                    _model=schema
                )
        except tuple(DISCOVERY_EXCEPTIONS.keys()) as schema_discovery_error:
            cls.logger.error(
                DISCOVERY_EXCEPTIONS.get(type(schema_discovery_error), f'Error while discovering schemas: {schema_discovery_error}')
            )
            raise schema_discovery_error

        cls.logger.info(
            f'Available schemas: {", ".join(discovered_schemas.keys())}'
        )
        return discovered_schemas

    @classmethod
    def __discover_schemas(cls, target_path: str) -> list[type[TranspiledSchema]]:
        cls.logger.info(f'Discovering schemas in: {target_path}')
        schemas: list[type[TranspiledSchema]] = []
        for schema in os.listdir(target_path):
            if schema.startswith('_'):
                continue

            schema_path = f'{target_path}/{schema}'
            if not os.path.isdir(schema_path):
                cls.logger.info(f'Importing schema: {schema_path}')

                with open(schema_path, 'r', encoding='utf-8') as schema_file:
                    schema_data = yaml.safe_load(schema_file)
                    cls.load_schema(schema_data)
                continue

            nested_schemas = cls.__discover_schemas(schema_path)
            schemas.extend(nested_schemas)
        return schemas

    @classmethod
    def load_schema(cls, schema: SchemaInputFile) -> str:
        cls.logger.info(f'Loading schema: {schema["name"]}')
        schema_class = Transpiler.make_schema(schema)
        cls._schemas[schema['name']] = SchemaInstancesFactory(
            name=schema_class.transpilation_name,
            _model=schema_class
        )
        return schema_class.transpilation_name
