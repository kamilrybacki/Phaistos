# pylint: disable=protected-access, too-few-public-methods
from __future__ import annotations
import dataclasses
import logging
import pydoc
import typing

import phaistos.consts
import phaistos.schema
import phaistos.sources
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
import phaistos.utils


@dataclasses.dataclass
class Transpiler:
    _logger: typing.ClassVar[logging.Logger] = phaistos.consts.TRANSPILATION_LOGGER

    def __post_init__(self) -> None:
        self._logger.info(f'{self.__class__.__name__} is a stateless interface, and instantiation is not necessary.')

    # pylint: disable=unnecessary-lambda-assignment
    @classmethod
    def make_validator(cls, prop: ParsedProperty) -> CompiledValidator | None:
        """
        Method to transpile a property's validator into a Pydantic model field validator.

        Args:
            prop (ParsedProperty): A property with its respective data, from which the validator will be extracted.

        Returns:
            TranspiledPropertyValidator: A Pydantic model field validator.
        """
        if 'validator' not in prop['data']:
            return None
        return ValidationFunctionsCompiler.compile(prop)

    @classmethod
    def make_property(cls, prop: ParsedProperty) -> TranspiledProperty:
        """
        Method to transpile a property into a Pydantic model field.

        Args:
            prop (ParsedProperty): A property with its respective data.

        Returns:
            TranspiledProperty: A Pydantic model field.
        """
        if 'properties' not in prop['data']:
            adjusted_data = phaistos.utils.adjust_collection_type_property_entry(prop)
            return TranspiledProperty(
                type=pydoc.locate(  # type: ignore
                    path=str(
                        adjusted_data['data'].get('type')
                    )
                ),
                default=adjusted_data['data'].get('default', ...),
                validator=cls.make_validator(adjusted_data),
                constraints=adjusted_data['data'].get('constraints', {})
            )
        return TranspiledProperty(
            type=cls.make_schema({
                'name': prop['name'],
                'version': prop['data'].get('version', '...'),  # type: ignore
                'description': prop['data'].get('description', ''),
                'properties': prop['data']['properties'],
                'context': prop['data'].get('context', {}),  # type: ignore
                'validator': prop['data'].get('validator', RawValidator({
                    'source': 'pass',
                    'mode': 'before'
                }))
            }),
            default=...,
            validator=cls.make_validator(prop),
            constraints={}
        )

    @classmethod
    def make_properties(cls, properties: list[ParsedProperty]) -> TranspiledModelData:
        """
        Method to read a list of properties and transpile them into a Pydantic model fields.

        Args:
            properties (list[ParsedProperty]): A list of properties with their respective data.

        Returns:
            TranspiledModelData: A dictionary with the transpiled properties.
        """
        transpiled_model_data: dict[str, TranspiledProperty] = {
            prop['name']: cls.make_property(prop)
            for prop in properties
        }
        properties_annotations: typing.Dict[str, typing.Any] = {
            property_name: phaistos.utils.construct_field_annotation(property_data)
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

    @classmethod
    def make_schema(cls, schema: SchemaInputFile) -> type[TranspiledSchema]:
        """
        Transpile a schema into a Pydantic model.

        Args:
            schema (SchemaInputFile): A parsed schema, stored as a dictionary with typed fields.

        Returns:
            type[TranspiledSchema]: A Pydantic model class with the schema's properties.
        """
        cls._logger.info(f"Transpiling schema: {schema['name']}")

        transpilation = cls.make_properties([
            ParsedProperty(
                name=property_name,
                data=property_data
            )
            for property_name, property_data in schema['properties'].items()
        ])

        transpilation['context'] = schema.get('context', {})  # type: ignore

        if 'validator' in schema:
            cls._logger.info(f'Compiling {schema["name"]} model validator')
            validator_source = schema['validator'] if isinstance(schema['validator'], str) else schema['validator']['source']
            global_model_validator_function = ValidationFunctionsCompiler._compile_validator({
                'name': f'validate_{schema["name"].lower()}',
                'decorator': '@classmethod',
                'source': validator_source,
                'kind': 'model'
            })
            transpilation['global_validator'] = global_model_validator_function

        print(transpilation)

        transpiled_property_names = ', '.join([
            key
            for key in transpilation['properties'].keys()
            if not key.startswith('_')
        ])
        cls._logger.info(f"Schema {schema['name']} has been transpiled successfully. Transpiled properties: {transpiled_property_names}")

        class _Schema(TranspiledSchema):
            version: typing.ClassVar[str] = schema.get('version', '')
            description: typing.ClassVar[str] = schema.get('description', '')

        return _Schema.compile(
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
