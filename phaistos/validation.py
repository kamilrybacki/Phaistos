from __future__ import annotations
import dataclasses
import enum
import importlib
import logging
import os

import pydantic

from phaistos.types.schema import TranspiledSchema
from phaistos.consts import DISCOVERY_EXCEPTIONS
from phaistos.exceptions import SchemaParsingException


def _discover_schemas(target_path: str) -> list[type[TranspiledSchema]]:
    schemas: list[type[TranspiledSchema]] = []
    for schema in os.listdir(target_path):
        if schema.startswith('_'):
            continue

        schema_path = f'{target_path}/{schema}'
        if not os.path.isdir(schema_path):
            logging.info(f'Importing schema: {schema_path}')

            try:
                schema_class = getattr(
                    importlib.import_module(schema_path),
                    'Schema'
                )
            except AttributeError:
                logging.info(
                    f'No Schema class found in {schema}'
                )
                continue

            if not issubclass(schema_class, TranspiledSchema):
                logging.info(
                    f'Schema {schema} is not a valid schema'
                )
                continue
            if schema_class.__tag__ in [schema.__tag__ for schema in schemas]:
                logging.info(
                    f'Schema {schema} is already registered'
                )
                continue
            schemas.append(schema_class)
            continue

        schemas.extend(
            _discover_schemas(schema_path)
        )
    return schemas


def _get_available_schemas() -> enum.Enum:
    class _RegisteredSchemas(enum.Enum):
        pass

    try:
        for schema in _discover_schemas(
            os.environ['PHAISTOS__SCHEMA_PATH']
        ):
            setattr(_RegisteredSchemas, str(schema.__tag__), schema)
    except tuple(DISCOVERY_EXCEPTIONS.keys()) as schema_discovery_error:
        logging.error(
            DISCOVERY_EXCEPTIONS.get(type(schema_discovery_error), f'Error while discovering schemas: {schema_discovery_error}')
        )
        raise schema_discovery_error

    return _RegisteredSchemas  # type: ignore


AvailableSchemas = enum.Enum('AvailableSchemas', {}) if os.environ.get('PHAISTOS__DISABLE_SCHEMA_DISCOVERY') else _get_available_schemas()


# pylint: disable=invalid-name
class _SchemaLoader:  # pylint: disable=too-few-public-methods
    cache: dict[str, ValidationSchema] = {}

    @classmethod
    def load(cls, name: str) -> type[TranspiledSchema]:
        schema = getattr(
            AvailableSchemas,
            name
        )
        if not issubclass(schema, TranspiledSchema):
            raise SchemaParsingException(
                f'Schema {name} is not a valid schema'
            )
        cls.cache[name] = schema
        return schema


@dataclasses.dataclass(frozen=True, kw_only=True)
class ValidationSchema:
    name: str

    _model: type[TranspiledSchema]

    @classmethod
    def construct(cls, name: str) -> ValidationSchema:
        if name not in _SchemaLoader.cache:
            _SchemaLoader.cache[name] = ValidationSchema(
                name=name,
                _model=_SchemaLoader.load(name)  # type: ignore
            )
        return _SchemaLoader.cache[name]

    def validate(self, data: dict) -> ValidationResults:
        try:
            self._model(**data)
            return ValidationResults(
                valid=True,
                schema=self._model.model_json_schema(),
                errors=[],
                data=data
            )
        except pydantic.ValidationError as validation_error:
            return ValidationResults(
                valid=False,
                schema=self._model.model_json_schema(),
                errors=[
                    FieldValidationError(
                        name=str(error['loc'][0]),
                        message=error['msg']
                    )
                    for error in validation_error.errors()
                ],
                data=data
            )


@dataclasses.dataclass(frozen=True, kw_only=True)
class FieldValidationError:
    name: str
    message: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class ValidationResults:
    valid: bool
    schema: dict
    errors: list[FieldValidationError]
    data: dict = dataclasses.field(default_factory=dict)


def against_schema(data: dict, schema: str) -> ValidationResults:
    return ValidationSchema.construct(schema).validate(data)
