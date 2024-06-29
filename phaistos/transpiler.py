# pylint: disable=protected-access, too-few-public-methods
from __future__ import annotations
import dataclasses
import logging
import pydoc
import re
import typing
import types

import pydantic

import phaistos.consts
import phaistos.exceptions
from phaistos.typings import (
    ParsedProperty,
    TranspiledProperty,
    TranspiledModelData,
    TranspiledPropertyValidator,
)
from phaistos.schema import TranspiledSchema

logging.basicConfig(level=logging.INFO)


@dataclasses.dataclass
class Transpiler:
    _logger: typing.ClassVar[logging.Logger] = phaistos.consts.TRANSPILATION_LOGGER

    def __post_init__(self) -> None:
        self._logger.info(f'{self.__class__.__name__} is a stateless interface, and instantiation is not necessary.')

    # pylint: disable=unnecessary-lambda-assignment
    @classmethod
    def validator(cls, prop: ParsedProperty) -> TranspiledPropertyValidator:
        validator_key = phaistos.consts.VALIDATOR_FUNCTION_NAME_TEMPLATE % prop['name']
        rendered_function_source_code = phaistos.consts.VALIDATOR_FUNCTION_SOURCE_TEMPLATE % (
            validator_key,
            prop['data'].get('validator', '').replace(
                '\n',
                f'\n{phaistos.consts.DEFAULT_INDENTATION}'
            )
        )
        temporary_module = types.ModuleType('temporary_module')
        temporary_module.__dict__.update(
            phaistos.consts.ISOLATION_FROM_UNWANTED_LIBRARIES
        )
        exec(  # pylint: disable=exec-used
            rendered_function_source_code,
            temporary_module.__dict__
        )
        validator_function = getattr(temporary_module, validator_key)
        return TranspiledPropertyValidator(
            field=prop['name'],
            name=validator_key,
            method=pydantic.field_validator(
                prop['name'],
                mode='after',
                check_fields=True,
            )(validator_function)
        )

    @classmethod
    def property(cls, prop: ParsedProperty) -> TranspiledProperty:
        if 'properties' not in prop['data']:
            cls._adjust_if_collection_type_is_used(prop)
            return TranspiledProperty(
                type=pydoc.locate(  # type: ignore
                    path=str(
                        prop['data'].get('type')
                    )
                ),
                default=prop['data'].get('default', ...),
                validator=cls.validator(prop),
            )
        return cls._transpile_nested_property(prop)

    @classmethod
    def _adjust_if_collection_type_is_used(cls, prop: ParsedProperty) -> None:
        if match := re.match(
            phaistos.consts.COLLECTION_TYPE_REGEX,
            prop['data']['type']
        ):
            cls._check_if_collection_type_is_allowed(match['collection'])
            prop['data']['validator'] = prop['data'].get('validator', '') + phaistos.consts.COLLECTION_VALIDATOR_TEMPLATE % (
                match['item'],
                prop['name'],
                match['item']
            )
            prop['data']['type'] = match['collection']

    @staticmethod
    def _check_if_collection_type_is_allowed(collection_type: str) -> None:
        if collection_type not in phaistos.consts.ALLOWED_COLLECTION_TYPES:
            raise phaistos.exceptions.IncorrectFieldTypeError(collection_type)

    @classmethod
    def _transpile_nested_property(cls, prop: ParsedProperty) -> TranspiledProperty:
        class NestedPropertySchema(TranspiledSchema):
            __tag__ = prop['name'].upper()

        NestedPropertySchema.__name__ = f'{prop["name"].capitalize()}Schema'
        nested_model_transpilation = cls.properties([
            ParsedProperty(
                name=property_name,
                data=property_data
            )
            for property_name, property_data in prop['data']['properties'].items()
        ])
        compiled_nested_schema = NestedPropertySchema.compile(
            prop['name'],
            nested_model_transpilation
        )
        return TranspiledProperty(
            type=compiled_nested_schema,
            default=...,
            validator=cls.validator(prop)
        )

    @classmethod
    def properties(cls, properties: list[ParsedProperty]) -> TranspiledModelData:
        transpiled_model_data: dict[str, TranspiledProperty] = {
            prop['name']: cls.property(prop)
            for prop in properties
        }
        properties_annotations: typing.Dict[str, typing.Any] = {
            property_name: (property_data['type'], property_data['default'])
            for property_name, property_data in transpiled_model_data.items()
            if not isinstance(property_data, type)
        } | {
            property_name: property_data
            for property_name, property_data in transpiled_model_data.items()
            if isinstance(property_data, type)
        }
        return TranspiledModelData(
            validators=[
                property_data['validator']
                for property_data in transpiled_model_data.values()
                if not isinstance(property_data, type)
            ],
            properties=properties_annotations
        )

    @classmethod
    def schema(cls, schema: dict[str, typing.Any]) -> type[TranspiledSchema]:
        cls._logger.info(f"Transpiling schema: {schema['name']}")

        class RootSchema(TranspiledSchema):
            __tag__: typing.ClassVar[str] = schema['name'].upper()
            version: typing.ClassVar[str] = schema['version']
            description: typing.ClassVar[str] = schema['description']

        transpilation = cls.properties([
            ParsedProperty(
                name=property_name,
                data=property_data
            )
            for property_name, property_data in schema['properties'].items()
        ])

        transpiled_property_names = ', '.join([
            key
            for key in transpilation['properties'].keys()
            if not key.startswith('_')
        ])
        cls._logger.info(f"Schema {schema['name']} has been transpiled successfully. Transpiled properties: {transpiled_property_names}")

        return RootSchema.compile(
            schema['name'],
            transpilation
        )

    @classmethod
    def supress_logging(cls) -> None:
        if cls._logger.level != logging.CRITICAL:
            cls._logger.setLevel(logging.CRITICAL)

    @classmethod
    def enable_logging(cls) -> None:
        if cls._logger.level != logging.INFO:
            cls._logger.setLevel(logging.INFO)
