# pylint: disable=protected-access, too-few-public-methods
from __future__ import annotations
import dataclasses
import copy
import logging
import pydoc
import re
import typing

import pydantic
import pydantic_core

import phaistos.consts
import phaistos.schema
import phaistos.sources
import phaistos.exceptions
from phaistos.typings import (
    SchemaInputFile,
    ParsedProperty,
    TranspiledProperty,
    TranspiledModelData,
    CompiledValidator,
    RawValidator
)
from phaistos.schema import TranspiledSchema
from phaistos.compiler import ValidationFunctionsCompiler

logging.basicConfig(level=logging.INFO)


@dataclasses.dataclass
class Transpiler:
    _logger: typing.ClassVar[logging.Logger] = phaistos.consts.TRANSPILATION_LOGGER

    def __post_init__(self) -> None:
        self._logger.info(f'{self.__class__.__name__} is a stateless interface, and instantiation is not necessary.')

    # pylint: disable=unnecessary-lambda-assignment
    @classmethod
    def validator(cls, prop: ParsedProperty) -> CompiledValidator | None:
        """
        Method to transpile a property's validator into a Pydantic model field validator.

        Args:
            prop (ParsedProperty): A property with its respective data, from which the validator will be extracted.

        Returns:
            TranspiledPropertyValidator: A Pydantic model field validator.
        """
        if 'validator' not in prop['data']:
            return None
        if isinstance(prop['data']['validator'], str):
            prop['data']['validator'] = RawValidator({
                'source': prop['data']['validator'],
                'mode': 'after' if 'type' in prop['data'] else 'before'
            })
        return ValidationFunctionsCompiler.compile(prop)

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
        return TranspiledProperty(
            type=cls.schema({
                'name': prop['name'],
                'version': prop['data'].get('version', '...'),  # type: ignore
                'description': prop['data'].get('description', ''),
                'properties': prop['data']['properties'],
            }),
            default=...,
            validator=cls.validator(prop),
            constraints={}
        )

    @classmethod
    def _adjust_if_collection_type_is_used(cls, prop: ParsedProperty) -> ParsedProperty:
        adjusted = copy.deepcopy(prop)
        validator_data = adjusted['data'].get('validator', RawValidator({
            'source': '',
            'mode': 'after'
        }))
        if match := re.match(
            phaistos.consts.COLLECTION_TYPE_REGEX,
            adjusted['data']['type']
        ):
            cls._check_if_collection_type_is_allowed(match['collection'])
            adjusted['data']['validator'] = RawValidator(
                source=validator_data['source'] + phaistos.sources.COLLECTION_VALIDATOR_TEMPLATE % (
                    match['item'],
                    adjusted['name'],
                    match['item']
                ),
                mode=validator_data['mode']
            )
            adjusted['data']['type'] = match['collection']
        else:
            adjusted['data']['validator'] = validator_data
        return adjusted

    @staticmethod
    def _check_if_collection_type_is_allowed(collection_type: str) -> None:
        if collection_type not in phaistos.consts.ALLOWED_COLLECTION_TYPES:
            raise phaistos.exceptions.IncorrectFieldTypeError(collection_type)

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
            validators=[
                validator
                for property_data in transpiled_model_data.values()
                if not isinstance(property_data, type)
                if (validator := property_data.get('validator')) is not None
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

        transpilation = cls.properties([
            ParsedProperty(
                name=property_name,
                data=property_data
            )
            for property_name, property_data in schema['properties'].items()
        ])

        transpilation['context'] = schema.get('context', {})  # type: ignore

        if 'validator' in schema:
            cls._logger.info('Compiling global model validator')
            global_model_validator_function = ValidationFunctionsCompiler._compile_validator_function(
                f'validate_{schema['name'].lower()}',
                schema['validator']['source'],
                kind='model'
            )
            transpilation['global_validator'] = global_model_validator_function

        transpiled_property_names = ', '.join([
            key
            for key in transpilation['properties'].keys()
            if not key.startswith('_')
        ])
        cls._logger.info(f"Schema {schema['name']} has been transpiled successfully. Transpiled properties: {transpiled_property_names}")

        class RootSchema(TranspiledSchema):
            version: typing.ClassVar[str] = schema.get('version', '')
            description: typing.ClassVar[str] = schema.get('description', '')

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
