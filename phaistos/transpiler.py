# pylint: disable=protected-access, too-few-public-methods
from __future__ import annotations
import dataclasses
import copy
import logging
import pydoc
import re
import typing
import types

import pydantic
import pydantic_core

import phaistos.consts
import phaistos.exceptions
from phaistos.typings import (
    SchemaInputFile,
    ParsedProperty,
    TranspiledProperty,
    TranspiledModelData,
    TranspiledValidator,
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
    def validator(cls, prop: ParsedProperty) -> TranspiledValidator:
        """
        Method to transpile a property's validator into a Pydantic model field validator.

        Args:
            prop (ParsedProperty): A property with its respective data, from which the validator will be extracted.

        Returns:
            TranspiledPropertyValidator: A Pydantic model field validator.
        """
        if 'type' in prop['data']:
            return cls._construct_field_validator(prop)
        return cls._construct_model_validator(prop)

    @classmethod
    def _construct_field_validator(cls, prop: ParsedProperty) -> TranspiledValidator:
        validator_key = phaistos.consts.FIELD_VALIDATOR_FUNCTION_NAME_TEMPLATE % prop['name']
        rendered_function_source_code = phaistos.consts.FIELD_VALIDATOR_FUNCTION_SOURCE_TEMPLATE % (
            validator_key,
            prop['data'].get('validator', '').replace(
                '\n',
                f'\n{phaistos.consts.DEFAULT_INDENTATION}'
            )
        )
        validator_function = cls._compile_validator_function(
            validator_key,
            rendered_function_source_code
        )
        return TranspiledValidator(
            field=prop['name'],
            name=validator_key,
            method=pydantic.field_validator(
                prop['name'],
                mode='after',
                check_fields=True,
            )(validator_function)
        )

    @classmethod
    def _compile_validator_function(cls, name: str, source: str) -> types.FunctionType:
        temporary_module = types.ModuleType('temporary_module')
        temporary_module.__dict__.update(
            phaistos.consts.ISOLATION_FROM_UNWANTED_LIBRARIES
        )
        exec(  # pylint: disable=exec-used
            source,
            temporary_module.__dict__
        )
        return getattr(temporary_module, name)

    @classmethod
    def _construct_model_validator(cls, prop: ParsedProperty) -> TranspiledValidator:
        rendered_function_source_code = phaistos.consts.MODEL_VALIDATOR_FUNCTION_SOURCE_TEMPLATE % (
            prop['data'].get('validator', '').replace(
                '\n',
                f'\n{phaistos.consts.DEFAULT_INDENTATION}'
            )
        )
        validator_function = cls._compile_validator_function(
            phaistos.consts.MODEL_VALIDATOR_FUNCTION_NAME,
            rendered_function_source_code
        )
        return TranspiledValidator(
            field='__root__',
            name=phaistos.consts.MODEL_VALIDATOR_FUNCTION_NAME,
            method=pydantic.model_validator(
                mode='after',
            )(validator_function)
        )

    @classmethod
    def property(cls, prop: ParsedProperty) -> TranspiledProperty:
        """
        Method to transpile a property into a Pydantic model field.

        Args:
            prop (ParsedProperty): A property with its respective data.

        Returns:
            TranspiledProperty: A Pydantic model field.
        """
        if 'properties' not in prop['data']:
            adjusted_data = cls._adjust_if_collection_type_is_used(prop)
            return TranspiledProperty(
                type=pydoc.locate(  # type: ignore
                    path=str(
                        adjusted_data['data'].get('type')
                    )
                ),
                default=adjusted_data['data'].get('default', ...),
                validator=cls.validator(adjusted_data),
                constraints=adjusted_data['data'].get('constraints', {})
            )
        return cls._transpile_nested_property(prop)

    @classmethod
    def _adjust_if_collection_type_is_used(cls, prop: ParsedProperty) -> ParsedProperty:
        adjusted = copy.deepcopy(prop)
        if match := re.match(
            phaistos.consts.COLLECTION_TYPE_REGEX,
            adjusted['data']['type']
        ):
            cls._check_if_collection_type_is_allowed(match['collection'])
            adjusted['data']['validator'] = adjusted['data'].get('validator', '') + phaistos.consts.COLLECTION_VALIDATOR_TEMPLATE % (
                match['item'],
                adjusted['name'],
                match['item']
            )
            adjusted['data']['type'] = match['collection']
        return adjusted

    @staticmethod
    def _check_if_collection_type_is_allowed(collection_type: str) -> None:
        if collection_type not in phaistos.consts.ALLOWED_COLLECTION_TYPES:
            raise phaistos.exceptions.IncorrectFieldTypeError(collection_type)

    @classmethod
    def _transpile_nested_property(cls, prop: ParsedProperty) -> TranspiledProperty:
        class NestedPropertySchema(TranspiledSchema):
            pass

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
            validator=cls.validator(prop),
            constraints={}
        )

    @classmethod
    def properties(cls, properties: list[ParsedProperty]) -> TranspiledModelData:
        """
        Method to read a list of properties and transpile them into a Pydantic model fields.

        Args:
            properties (list[ParsedProperty]): A list of properties with their respective data.

        Returns:
            TranspiledModelData: A dictionary with the transpiled properties.
        """
        transpiled_model_data: dict[str, TranspiledProperty] = {
            prop['name']: cls.property(prop)
            for prop in properties
        }
        properties_annotations: typing.Dict[str, typing.Any] = {
            property_name: cls._construct_field_annotation(property_data)
            for property_name, property_data in transpiled_model_data.items()
            if not isinstance(property_data, type)
        } | {
            property_name: property_data
            for property_name, property_data in transpiled_model_data.items()
            if isinstance(property_data, type)
        }
        return TranspiledModelData(
            validator=[
                property_data['validator']
                for property_data in transpiled_model_data.values()
                if not isinstance(property_data, type)
            ],
            properties=properties_annotations
        )

    @staticmethod
    def _construct_field_annotation(property_data: TranspiledProperty) -> tuple[type, pydantic.fields.FieldInfo]:
        return (
            property_data['type'],
            pydantic.fields.FieldInfo(
                default=property_data.get(
                    'default',
                    pydantic_core.PydanticUndefined
                ),
                **property_data['constraints']
            )
        )

    @classmethod
    def schema(cls, schema: SchemaInputFile) -> type[TranspiledSchema]:
        """
        Transpile a schema into a Pydantic model.

        Args:
            schema (SchemaInputFile): A parsed schema, stored as a dictionary with typed fields.

        Returns:
            type[TranspiledSchema]: A Pydantic model class with the schema's properties.
        """
        cls._logger.info(f"Transpiling schema: {schema['name']}")

        class RootSchema(TranspiledSchema):
            version: typing.ClassVar[str] = schema['version']
            description: typing.ClassVar[str] = schema['description']

        transpilation = cls.properties([
            ParsedProperty(
                name=property_name,
                data=property_data
            )
            for property_name, property_data in schema['properties'].items()
        ])

        transpilation['context'] = schema.get('context', {})  # type: ignore

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
