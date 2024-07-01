from collections import ChainMap
import typing

import pytest

import conftest  # type: ignore
import consts  # type: ignore

from phaistos.transpiler import Transpiler
from phaistos.schema import TranspiledSchema
from phaistos.consts import BLOCKED_MODULES
from phaistos.exceptions import ForbiddenModuleUseInValidator


def _check_transpiled_validator(
    data: typing.Any,
    validator: typing.Callable,
    logger
) -> None:
    with pytest.raises(ValueError):
        validator(data)
    logger.info(f'Invalid data "{data}" caught successfully')


def _extract_transpiled_validators(
    transpiled_schema: type[TranspiledSchema],
    validators_to_check: list[tuple[str, str, list]]
) -> dict[str, tuple[typing.Any | None, list]]:
    validators_found = {
        validator[1]: (
            getattr(transpiled_schema, validator[1], None),
            validator[2],
        )
        for validator in validators_to_check
    }
    validators_left = [
        validator
        for validator in validators_to_check
        if validators_found[validator[1]][0] is None
    ]
    for property_data in transpiled_schema.__dict__['__annotations__'].values():
        if '__pydantic_complete__' in property_data.__dict__:
            validators_found |= _extract_transpiled_validators(
                transpiled_schema=property_data,
                validators_to_check=validators_left,
            )
    return validators_found


@pytest.mark.order(1)
@pytest.mark.parametrize(
    'patch',
    consts.MOCK_SCHEMA_PATCHES,
    ids=[
        '|'.join(patch.keys())
        for patch in consts.MOCK_SCHEMA_PATCHES
    ]
)
def test_patched_schema_transpilation(patch: dict, mock_config_file_base, logger) -> None:
    logger.info('Testing schema transpilation for patch: %s', {
        property: patch[property]['type'] if 'type' in patch[property] else 'nested'
        for property in patch
    })
    transpiled_schema = Transpiler.schema(
        schema=mock_config_file_base | {
            'properties': patch
        }
    )
    mock_schema_test_data = conftest.create_mock_schema_data(
        applied_properties=patch
    )
    logger.info('Validating clean data: %s', mock_schema_test_data)
    assert transpiled_schema(**mock_schema_test_data)

    validators_to_check = conftest.find_custom_validators(patch)

    logger.info('Checking if validators are present: %s', [
        validator_to_check[1]
        for validator_to_check in validators_to_check
    ])
    validator_check_results = _extract_transpiled_validators(transpiled_schema, validators_to_check)

    assert all(
        result[0] is not None
        for result in validator_check_results.values()
    )

    for validator in validator_check_results.values():
        for sample in validator[1]:
            _check_transpiled_validator(
                data=sample,
                validator=validator[0],  # type: ignore
                logger=logger
            )


@pytest.mark.order(2)
def test_merged_schema(mock_config_file_base, logger) -> None:
    logger.info('Testing schema transpilation for schema merged from ALL previous patches')
    test_patched_schema_transpilation(
        patch=dict(
            ChainMap(*consts.MOCK_SCHEMA_PATCHES)
        ),
        mock_config_file_base=mock_config_file_base,
        logger=logger
    )


@pytest.mark.order(3)
@pytest.mark.parametrize(
    'blocked_module',
    BLOCKED_MODULES,
    ids=BLOCKED_MODULES
)
def test_module_shadowing(blocked_module, mock_config_file_base, logger) -> None:
    logger.info(f'Testing module shadowing for module: {blocked_module}')
    try:
        Transpiler.supress_logging()
        forbidden_schema = Transpiler.schema(
            schema=mock_config_file_base | {
                'properties': {
                    'text': {
                        'description': 'Text to be displayed',
                        'type': 'str',
                        'validator': f'if {blocked_module}.LOCK: {blocked_module}.some_attribute'
                    }
                }
            }
        )
        forbidden_schema(text=f'Hello, {blocked_module}!')
    except ForbiddenModuleUseInValidator:
        Transpiler.enable_logging()
        return


@pytest.mark.order(4)
@pytest.mark.parametrize(
    'exploit',
    consts.VULNERABILITIES_TO_TEST,
    ids=[
        exploit['name']
        for exploit in consts.VULNERABILITIES_TO_TEST
    ]
)
def test_possible_exploits(exploit: dict[str, str], mock_config_file_base) -> None:
    try:
        schema = Transpiler.schema(
            schema=mock_config_file_base | {
                'properties': {
                    'whatever': {
                        'description': 'We care only about the validator',
                        'type': 'int',
                        'validator': exploit['code']
                    }
                }
            }
        )
        schema(whatever=42)  # type: ignore
    except ForbiddenModuleUseInValidator:
        return
    pytest.fail(f'Exploit "{exploit["name"]}" wasn\'t prevented!')
