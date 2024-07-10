import logging
import types
import typing

import pydantic

import phaistos.consts
import phaistos.sources
from phaistos.typings import (
    ParsedProperty,
    CompiledValidator,
    RawValidator
)
import phaistos.utils


class ValidationFunctionsCompiler:
    _logger: typing.ClassVar[logging.Logger] = phaistos.consts.COMPILATION_LOGGER

    @classmethod
    def compile(cls, prop: ParsedProperty) -> CompiledValidator:
        if isinstance(prop['data']['validator'], str):
            prop['data']['validator'] = RawValidator({
                'source': prop['data']['validator'],
                'mode': 'after' if 'type' in prop['data'] else 'before'
            })
        phaistos.utils.check_for_forbidden_imports(
            source=prop['data']['validator']['source']
        )
        return cls._compile_for_model(prop) \
            if 'type' not in prop['data'] \
            else cls._compile_for_field(prop)

    @classmethod
    def _compile_for_field(cls, prop: ParsedProperty) -> CompiledValidator:
        cls._logger.info(f'Compiling field validator for {prop["name"]}')
        validator_key = phaistos.sources.FIELD_VALIDATOR_FUNCTION_NAME_TEMPLATE % prop['name']
        validator_function = cls._compile_validator({
            'name': validator_key,
            'source': prop['data']['validator']['source'],
            'kind': 'field',
            'decorator': '@classmethod',
            'extra_arguments': ''
        })
        return CompiledValidator(
            field=prop['name'],
            name=validator_key,
            method=pydantic.field_validator(
                prop['name'],
                mode=prop['data']['validator']['mode'],
                check_fields=True,
            )(validator_function)
        )

    @classmethod
    def _compile_for_model(cls, prop: ParsedProperty) -> CompiledValidator:
        cls._logger.info(f'Compiling {prop['name']} model validator')
        validator_function = cls._compile_validator({
            'name': phaistos.sources.MODEL_VALIDATOR_FUNCTION_NAME,
            'source': prop['data']['validator']['source'],
            'kind': 'model',
            'decorator': '@classmethod' if prop['data']['validator']['mode'] == 'before' else '',
        })
        return CompiledValidator(
            field=prop['name'],
            name=phaistos.sources.MODEL_VALIDATOR_FUNCTION_NAME,
            method=validator_function
        )

    @staticmethod
    def _compile_validator(data: dict[str, str]) -> types.FunctionType:
        template = phaistos.sources.FIELD_VALIDATOR_FUNCTION_SOURCE_TEMPLATE if data['kind'] == 'field' else phaistos.sources.MODEL_VALIDATOR_FUNCTION_SOURCE_TEMPLATE
        rendered_function_source_code = template % {
            'decorator': data.get('decorator', ''),
            'name': data['name'],
            'first_argument': 'cls' if data.get('decorator') == '@classmethod' else 'self',
            'extra_arguments': data.get('extra_arguments', ''),
            'source': data['source'].replace('\n', '\n  ')
        }
        temporary_module = types.ModuleType('temporary_module')
        temporary_module.__dict__.update(
            phaistos.consts.ISOLATION_FROM_UNWANTED_LIBRARIES
        )
        exec(  # pylint: disable=exec-used
            rendered_function_source_code,
            temporary_module.__dict__,
        )
        return getattr(temporary_module, data['name'])
