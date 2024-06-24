# pylint: disable=protected-access, too-few-public-methods
import pydoc
import typing
import types

import pydantic

import confjurer.consts
from confjurer.types.schema import BaseSchemaModel


def _transpile_properties(properties: dict[str, typing.Any]) -> dict[str, dict[str, typing.Any]]:
    transpiled_properties: dict[str, tuple] = {}
    transpiled_validators: dict[str, typing.Callable] = {}
    for name, field in properties.items():
        if 'properties' in field.keys():
            class PropertySchema(BaseSchemaModel):
                __tag__ = name.upper()
            PropertySchema.__name__ = f'{name.capitalize()}Schema'
            nested_model_transpilation = _transpile_properties(
                field.get('properties', {})
            )
            nested_schema_model = pydantic.create_model(  # type: ignore
                name,
                __base__=PropertySchema,
                __validators__=nested_model_transpilation['validators'],
                **nested_model_transpilation['properties']
            )
            transpiled_properties[name] = (nested_schema_model, ...)
        else:
            transpiled_properties[name] = (
                pydoc.locate(
                    path=str(field['type'])
                ),
                field.get('default', ...)
            )
            if 'validator' in field.keys():
                validator_name = f'{name}_validator'
                compiled_function = confjurer.consts.VALIDATOR_FUNCTION_TEMPLATE % (
                    validator_name,
                    field['validator'].replace(
                        '\n',
                        f'\n{confjurer.consts.INDENTATION}'
                    )
                )
                temporary_module = types.ModuleType('temporary_module')
                exec(compiled_function, temporary_module.__dict__)  # pylint: disable=exec-used
                validator_function = pydantic.field_validator(
                    name,
                    mode='before',
                    check_fields=True
                )(
                    getattr(temporary_module, validator_name)
                )
                transpiled_validators[f'{name}_validator'] = validator_function
    return {
        'properties': transpiled_properties,
        'validators': transpiled_validators
    }


def transpile_schema(schema: dict[str, typing.Any]) -> type[BaseSchemaModel]:
    class RootSchema(BaseSchemaModel):
        __tag__: typing.ClassVar[str] = schema['name'].upper()
        version: typing.ClassVar[str] = schema['version']
        description: typing.ClassVar[str] = schema['description']

        @classmethod
        def from_fields(
            cls,
            properties: dict[str, tuple],
            validators: dict[str, typing.Callable] | None = None
        ):
            return pydantic.create_model(  # type: ignore
                schema['name'],
                __base__=cls,
                __validators__=validators,
                **properties
            )

    return RootSchema.from_fields(
        **_transpile_properties(schema['properties'])
    )
