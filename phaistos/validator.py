from __future__ import annotations
import dataclasses
import enum
import importlib
import logging
import os
import typing

from phaistos.types import (
    TranspiledSchema,
    ValidationResults,
    ValidationSchema
)
from phaistos.consts import DISCOVERY_EXCEPTIONS, VALIDATION_LOGGER
from phaistos.exceptions import SchemaParsingException


@dataclasses.dataclass()
class Validator:
    _schemas: typing.ClassVar[enum.Enum] = enum.Enum('AvailableSchemas', {})
    _cache: typing.ClassVar[dict[str, ValidationSchema]] = {}
    _logger: typing.ClassVar[logging.Logger] = VALIDATION_LOGGER

    @classmethod
    def against_schema(cls, data: dict, schema: str) -> ValidationResults:
        cls._logger.info(f'Validating data against schema: {schema}')
        cls._logger.debug(f'Data: {data}')
        return ValidationSchema.construct(schema).validate(data, cls._logger)

    @classmethod
    def construct(cls, name: str) -> ValidationSchema:
        if name not in cls._cache:
            cls._cache[name] = ValidationSchema(
                name=name,
                _model=cls.__load(name)  # type: ignore
            )
        return cls._cache[name]

    @classmethod
    def __load(cls, name: str) -> type[TranspiledSchema]:
        cls._logger.info(f'Loading schema: {name}')
        schema = getattr(
            cls._schemas,
            name
        )
        if not issubclass(schema, TranspiledSchema):
            raise SchemaParsingException(
                f'Schema {name} is not a valid schema'
            )
        cls._cache[name] = schema
        return schema

    def __post_init__(self):
        self._schemas = enum.Enum('AvailableSchemas', {}) \
            if os.environ.get('PHAISTOS__DISABLE_SCHEMA_DISCOVERY') \
            else self.get_available_schemas()

    @classmethod
    def get_available_schemas(cls) -> enum.Enum:
        class _RegisteredSchemas(enum.Enum):
            pass

        try:
            for schema in cls.__discover_schemas(
                os.environ['PHAISTOS__SCHEMA_PATH']
            ):
                setattr(_RegisteredSchemas, str(schema.__tag__), schema)
        except tuple(DISCOVERY_EXCEPTIONS.keys()) as schema_discovery_error:
            cls._logger.error(
                DISCOVERY_EXCEPTIONS.get(type(schema_discovery_error), f'Error while discovering schemas: {schema_discovery_error}')
            )
            raise schema_discovery_error

        cls._logger.info(
            f'Available schemas: {", ".join([schema.__tag__ for schema in _RegisteredSchemas])}'
        )
        return _RegisteredSchemas  # type: ignore

    @classmethod
    def __discover_schemas(cls, target_path: str) -> list[type[TranspiledSchema]]:
        schemas: list[type[TranspiledSchema]] = []
        for schema in os.listdir(target_path):
            if schema.startswith('_'):
                continue

            schema_path = f'{target_path}/{schema}'
            if not os.path.isdir(schema_path):
                cls._logger.info(f'Importing schema: {schema_path}')

                try:
                    schema_class = getattr(
                        importlib.import_module(schema_path),
                        'Schema'
                    )
                except AttributeError:
                    cls._logger.error(f'No Schema class found in {schema}')
                    continue

                if not issubclass(schema_class, TranspiledSchema):
                    cls._logger.warning(f'Schema {schema} is not a valid schema')
                    continue
                if schema_class.__tag__ in [schema.__tag__ for schema in schemas]:
                    cls._logger.info(f'Schema {schema} is already registered')
                    continue
                schemas.append(schema_class)
                continue

            nested_schemas = cls.__discover_schemas(schema_path)
            schemas.extend(nested_schemas)
        return schemas
