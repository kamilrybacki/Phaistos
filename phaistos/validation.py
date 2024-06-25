from __future__ import annotations
import dataclasses
import enum
import importlib
import logging
import os

import pydantic

from phaistos.types.schema import TranspiledSchema

ROOT_SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), '..', 'schemas')


def _discover_schemas(directory: str) -> list[type[TranspiledSchema]]:
    schemas: list[type[TranspiledSchema]] = []
    for schema in os.listdir(directory):
        if schema.startswith('_'):
            continue

        absolute_path = f'{directory}/{schema}'
        if not os.path.isdir(absolute_path):
            import_path = 'phaistos.schemas.' + absolute_path \
                .split(ROOT_SCHEMAS_DIR)[1] \
                .removeprefix('/') \
                .replace('/', '.') \
                .removesuffix('.py')
            logging.info(f'Importing schema: {import_path}')

            try:
                schema_class = getattr(
                    importlib.import_module(import_path),
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
            _discover_schemas(absolute_path)
        )
    return schemas


def _get_available_schemas() -> enum.Enum:
    class _RegisteredSchemas(enum.Enum):
        pass

    for schema in _discover_schemas(ROOT_SCHEMAS_DIR):
        setattr(_RegisteredSchemas, str(schema.__tag__), schema)

    return _RegisteredSchemas  # type: ignore


AvailableSchemas = _get_available_schemas()


class SchemaParsingException(Exception):
    def __init__(self, message):
        super().__init__(message)


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
