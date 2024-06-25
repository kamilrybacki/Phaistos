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
from phaistos.types.schema import BaseSchemaModel, ParsedProperty, TranspiledProperty, TranspiledModelData

logging.basicConfig(level=logging.INFO)


@dataclasses.dataclass(frozen=True)
class Transpiler:
    _logger: typing.ClassVar[logging.Logger] = logging.getLogger(__name__.upper())

    def __post_init__(self) -> None:
        self._logger.info(f'{self.__class__.__name__} is a stateless interface, and instantiation is not necessary.')

    # pylint: disable=unnecessary-lambda-assignment
    @classmethod
    def validator(cls, prop: ParsedProperty) -> typing.Callable:
        validator_key = f'{prop["name"]}_validator'
        rendered_function_source_code = phaistos.consts.VALIDATOR_FUNCTION_TEMPLATE % (
            validator_key,
            prop['data'].get('validator', '').replace(
                '\n',
                f'\n{phaistos.consts.DEFAULT_INDENTATION}'
            )
        )
        print(rendered_function_source_code)
        temporary_module = types.ModuleType('temporary_module')
        exec(rendered_function_source_code, temporary_module.__dict__)  # pylint: disable=exec-used
        validator_function = getattr(temporary_module, validator_key)
        return pydantic.field_validator(
            prop['name'],
            mode='wrap',
            check_fields=True
        )(validator_function)

    @classmethod
    def property(cls, prop: ParsedProperty) -> TranspiledProperty:
        cls._logger.info(f"Transpiling property: {prop['name']}")
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
        class NestedPropertySchema(BaseSchemaModel):
            __tag__ = prop['name'].upper()

        NestedPropertySchema.__key__ = f'{prop["name"].capitalize()}Schema'
        nested_model_transpilation = cls.properties(
            prop['data'].get('properties', {})
        )
        nested_schema_model = pydantic.create_model(  # type: ignore
            prop['name'],
            __base__=NestedPropertySchema,
            **nested_model_transpilation
        )
        return TranspiledProperty(
            type=nested_schema_model,
            default=prop['data'].get('default', ...),
            validator=cls.validator(prop),
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
        }
        return {
            '__validators__': {
                property_name: property_data['validator']
                for property_name, property_data in transpiled_model_data.items()
            },
            **properties_annotations  # type: ignore
        }

    @classmethod
    def schema(cls, schema: dict[str, typing.Any]) -> type[BaseSchemaModel]:
        cls._logger.info(f"Transpiling schema: {schema['name']}")

        class RootSchema(BaseSchemaModel):
            __tag__: typing.ClassVar[str] = schema['name'].upper()
            version: typing.ClassVar[str] = schema['version']
            description: typing.ClassVar[str] = schema['description']

            @classmethod
            def compile(cls, model_data: TranspiledModelData) -> type[BaseSchemaModel]:
                return pydantic.create_model(
                    schema['name'],
                    __base__=cls,
                    **model_data
                )

        return RootSchema.compile(
            cls.properties([
                ParsedProperty(
                    name=property_name,
                    data=property_data
                )
                for property_name, property_data in schema['properties'].items()
            ])
        )

    @classmethod
    def supress_logging(cls) -> None:
        if cls._logger.level != logging.CRITICAL:
            cls._logger.setLevel(logging.CRITICAL)

    @classmethod
    def enable_logging(cls) -> None:
        if cls._logger.level != logging.INFO:
            cls._logger.setLevel(logging.INFO)
