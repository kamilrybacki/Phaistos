from __future__ import annotations
import logging
import os
import typing
import yaml

from phaistos.transpiler import Transpiler
from phaistos.typings import ValidationResults
from phaistos.schema import TranspiledSchema, ValidationSchema
from phaistos.consts import DISCOVERY_EXCEPTIONS, VALIDATION_LOGGER
from phaistos.exceptions import SchemaParsingException


class Validator:
    _schemas: dict[str, ValidationSchema] = {}
    _logger: typing.ClassVar[logging.Logger] = VALIDATION_LOGGER

    __instance: typing.ClassVar[Validator | None] = None
    __started: typing.ClassVar[bool] = False
    __last_used_schemas_dir: typing.ClassVar[str] = ''

    @classmethod
    def start(cls) -> Validator:
        if cls.__started and cls.__last_used_schemas_dir != os.environ.get('PHAISTOS__SCHEMA_PATH', ''):
            cls._logger.info('Schema path has changed. Reloading schemas.')
            cls.__instance = None
            cls.__started = False
        if not cls.__instance:
            cls._logger.info('Starting Phaistos validator!')
            cls.__started = True
            cls.__last_used_schemas_dir = os.environ.get('PHAISTOS__SCHEMA_PATH', '')
            cls.__instance = cls()
        return cls.__instance

    def __init__(self) -> None:
        if not self.__started:
            raise RuntimeError(
                'Validator must be started using Validator.start()'
            )
        if not os.environ.get('PHAISTOS__DISABLE_SCHEMA_DISCOVERY'):
            self._schemas = self.get_available_schemas()

    def against_schema(self, data: dict, schema: str) -> ValidationResults:
        self._logger.info(f'Validating data against schema: {schema}')
        return self.get_model(schema).validate(data)

    def get_model(self, name: str) -> ValidationSchema:
        if name not in self._schemas:
            self._schemas[name] = ValidationSchema(
                name=name,
                _model=self.__load(name)  # type: ignore
            )
        return self._schemas[name]

    def __load(self, name: str) -> type[TranspiledSchema]:
        self._logger.info(f'Loading schema: {name}')
        schema = self._schemas.get(name)
        if not isinstance(schema, TranspiledSchema):
            raise SchemaParsingException(
                f'Schema {name} is not a valid schema'
            )
        return schema

    def get_available_schemas(self, path: str = '') -> dict[str, ValidationSchema]:
        discovered_schemas = getattr(self, '_schemas', {})
        try:
            schemas_dir = path or os.environ['PHAISTOS__SCHEMA_PATH']
            for schema in self.__discover_schemas(schemas_dir):
                discovered_schemas[schema.__name__] = ValidationSchema(
                    name=schema.__name__,
                    _model=schema
                )
        except tuple(DISCOVERY_EXCEPTIONS.keys()) as schema_discovery_error:
            self._logger.error(
                DISCOVERY_EXCEPTIONS.get(type(schema_discovery_error), f'Error while discovering schemas: {schema_discovery_error}')
            )
            raise schema_discovery_error

        self._logger.info(
            f'Available schemas: {", ".join(discovered_schemas.keys())}'
        )
        return discovered_schemas

    def __discover_schemas(self, target_path: str) -> list[type[TranspiledSchema]]:
        self._logger.info(f'Discovering schemas in: {target_path}')
        schemas: list[type[TranspiledSchema]] = []
        for schema in os.listdir(target_path):
            if schema.startswith('_'):
                continue

            schema_path = f'{target_path}/{schema}'
            if not os.path.isdir(schema_path):
                self._logger.info(f'Importing schema: {schema_path}')

                with open(schema_path, 'r', encoding='utf-8') as schema_file:
                    schema_data = yaml.safe_load(schema_file)
                    schema_class = Transpiler.schema(schema_data)
                    schemas.append(schema_class)
                continue

            nested_schemas = self.__discover_schemas(schema_path)
            schemas.extend(nested_schemas)
        return schemas
