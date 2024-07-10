from __future__ import annotations
import dataclasses
import logging
import os
import typing
import yaml

import pydantic

from phaistos.transpiler import Transpiler
from phaistos.typings import (
    SchemaInputFile,
    FieldValidationErrorInfo,
    ValidationResults
)
from phaistos.schema import TranspiledSchema
from phaistos.consts import DISCOVERY_EXCEPTIONS, VALIDATION_LOGGER
from phaistos.exceptions import SchemaParsingException


@dataclasses.dataclass(kw_only=True)
class ValidationHandler:
    """
    A dataclass that represents a validation schema.

    Attributes:
        name (str): The name of the schema.
        _model (type[TranspiledSchema]): The model of the schema, used for validation.
    """
    name: str
    _model: type[TranspiledSchema]

    def validate(self, data: dict) -> ValidationResults:
        """
        Validate the given data against the schema. Do not return
        the validated data, only the validation results.

        Args:
            data (dict): The data to validate.

        Returns:
            ValidationResults: The validation results, including the schema, errors, and data.
        """
        collected_errors: list[FieldValidationErrorInfo] = []
        self._run_validators(data, collected_errors)
        return ValidationResults(
            valid=not collected_errors,
            schema=self._model.model_json_schema(),
            errors=collected_errors,
            data=data
        )

    def _run_validators(self, data: dict, collected_errors: list[FieldValidationErrorInfo]) -> None:
        try:
            self._model(**data)
        except pydantic.ValidationError as validation_error:
            collected_errors.extend([
                FieldValidationErrorInfo(
                    name=str(error['loc'][0]) if error['loc'] else '__root__',
                    message=error['msg']
                )
                for error in validation_error.errors()
            ])

    def __call__(self, *args: typing.Any, **kwds: typing.Any) -> TranspiledSchema:
        return self._model(*args, **kwds)


class Validator:
    _schemas: dict[str, ValidationHandler] = {}
    _logger: typing.ClassVar[logging.Logger] = VALIDATION_LOGGER

    __instance: typing.ClassVar[Validator | None] = None
    __started: typing.ClassVar[bool] = False
    __last_used_schemas_dir: typing.ClassVar[str] = ''

    def validate(self, data: dict, schema: str) -> ValidationResults:
        self._logger.info(f'Validating data against schema: {schema}')
        return self.get_model(schema).validate(data)

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

    def get_model(self, name: str) -> ValidationHandler:
        if name not in self._schemas:
            self._schemas[name] = ValidationHandler(
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

    def get_available_schemas(self, path: str = '') -> dict[str, ValidationHandler]:
        discovered_schemas = getattr(self, '_schemas', {})
        try:
            schemas_dir = path or os.environ['PHAISTOS__SCHEMA_PATH']
            for schema in self.__discover_schemas(schemas_dir):
                discovered_schemas[schema.__name__] = ValidationHandler(
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

    def load_schema(self, schema: SchemaInputFile) -> str:
        self._logger.info(f'Loading schema: {schema["name"]}')
        schema_class = Transpiler.schema(schema)
        self._schemas[schema_class.__name__] = ValidationHandler(
            name=schema_class.__name__,
            _model=schema_class
        )
        return schema_class.__name__

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
