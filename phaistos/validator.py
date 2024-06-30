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
    _schemas: typing.ClassVar[dict[str, ValidationSchema]] = {}
    _logger: typing.ClassVar[logging.Logger] = VALIDATION_LOGGER

    __instance: typing.ClassVar[Validator] = None
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

    @classmethod
    def against_schema(cls, data: dict, schema: str) -> ValidationResults:
        cls._logger.info(f'Validating data against schema: {schema}')
        return cls.construct(schema).validate(data)

    @classmethod
    def construct(cls, name: str) -> ValidationSchema:
        if name not in cls._schemas:
            cls._schemas[name] = ValidationSchema(
                name=name,
                _model=cls.__load(name)  # type: ignore
            )
        return cls._schemas[name]

    @classmethod
    def __load(cls, name: str) -> type[TranspiledSchema]:
        cls._logger.info(f'Loading schema: {name}')
        schema = cls._schemas.get(name)
        if not isinstance(schema, TranspiledSchema):
            raise SchemaParsingException(
                f'Schema {name} is not a valid schema'
            )
        return schema

    @classmethod
    def get_available_schemas(cls, path: str = '') -> dict[str, type[TranspiledSchema]]:
        discovered_schemas = getattr(cls, '_schemas', {})
        try:
            schemas_dir = path or os.environ['PHAISTOS__SCHEMA_PATH']
            for schema in cls.__discover_schemas(schemas_dir):
                discovered_schemas[schema.__name__] = ValidationSchema(
                    name=schema.__name__,
                    _model=schema
                )
        except tuple(DISCOVERY_EXCEPTIONS.keys()) as schema_discovery_error:
            cls._logger.error(
                DISCOVERY_EXCEPTIONS.get(type(schema_discovery_error), f'Error while discovering schemas: {schema_discovery_error}')
            )
            raise schema_discovery_error

        cls._logger.info(
            f'Available schemas: {", ".join(discovered_schemas.keys())}'
        )
        return discovered_schemas

    @classmethod
    def __discover_schemas(cls, target_path: str) -> list[type[TranspiledSchema]]:
        cls._logger.info(f'Discovering schemas in: {target_path}')
        schemas: list[type[TranspiledSchema]] = []
        for schema in os.listdir(target_path):
            if schema.startswith('_'):
                continue

            schema_path = f'{target_path}/{schema}'
            if not os.path.isdir(schema_path):
                cls._logger.info(f'Importing schema: {schema_path}')

                with open(schema_path, 'r', encoding='utf-8') as schema_file:
                    schema_data = yaml.safe_load(schema_file)
                    schema_class = Transpiler.schema(schema_data)
                    schemas.append(schema_class)
                continue

            nested_schemas = cls.__discover_schemas(schema_path)
            schemas.extend(nested_schemas)
        return schemas
