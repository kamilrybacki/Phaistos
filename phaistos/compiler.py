import logging
import types
import typing

import pydantic

import phaistos.consts
import phaistos.sources
from phaistos.typings import ParsedProperty, CompiledValidator


class ValidationFunctionsCompiler:
    _logger: typing.ClassVar[logging.Logger] = phaistos.consts.COMPILATION_LOGGER

    @classmethod
    def compile(cls, prop: ParsedProperty) -> CompiledValidator:
        cls._check_for_forbidden_imports(prop['data']['validator']['source'])
        if 'type' not in prop['data']:
            cls._logger.info('Compiling model validator')
            return cls._compile_model_validator(prop)
        cls._logger.info(f'Compiling field validator for {prop["name"]}')
        return cls._compile_field_validator(prop)

    @classmethod
    def _check_for_forbidden_imports(cls, source: str) -> None:
        if any(
            module in source
            for module in phaistos.consts.BLOCKED_MODULES
        ):
            raise phaistos.exceptions.ForbiddenModuleUseInValidator()

    @classmethod
    def _compile_field_validator(cls, prop: ParsedProperty) -> CompiledValidator:
        validator_key = phaistos.sources.FIELD_VALIDATOR_FUNCTION_NAME_TEMPLATE % prop['name']
        validator_function = cls._compile_validator_function(
            name=validator_key,
            source=prop['data']['validator']['source'],
            kind='field',
            decorator='@classmethod'
        )
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
    def _compile_model_validator(cls, prop: ParsedProperty) -> CompiledValidator:
        validator_function = cls._compile_validator_function(
            name=phaistos.sources.MODEL_VALIDATOR_FUNCTION_NAME,
            source=prop['data']['validator']['source'],
            kind='model',
            decorator='@classmethod' if prop['data']['validator']['mode'] == 'before' else '',
            extra_arguments='data: dict[str, typing.Any], '
        )
        return CompiledValidator(
            field='__root__',
            name=phaistos.sources.MODEL_VALIDATOR_FUNCTION_NAME,
            method=pydantic.model_validator(
                mode=prop['data']['validator']['mode'],
            )(validator_function)
        )

    @classmethod
    def _compile_validator_function(cls, name: str, source: str, kind: str, decorator: str = '', extra_arguments: str = '') -> types.FunctionType:
        template = phaistos.sources.FIELD_VALIDATOR_FUNCTION_SOURCE_TEMPLATE if kind == 'field' else phaistos.sources.MODEL_VALIDATOR_FUNCTION_SOURCE_TEMPLATE
        rendered_function_source_code = template % {
            'decorator': decorator,
            'name': name,
            'first_argument': 'cls' if decorator == '@classmethod' else 'self',
            'extra_arguments': extra_arguments,
            'source': source.replace('\n', '\n  ')
        }
        temporary_module = types.ModuleType('temporary_module')
        temporary_module.__dict__.update(
            phaistos.consts.ISOLATION_FROM_UNWANTED_LIBRARIES
        )
        exec(  # pylint: disable=exec-used
            rendered_function_source_code,
            temporary_module.__dict__
        )
        return getattr(temporary_module, name)
