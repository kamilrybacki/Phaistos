from collections import ChainMap
import typing

import pytest

import conftest
import consts

from phaistos.transpiler import Transpiler
from phaistos.types.schema import TranspiledSchema
from phaistos.consts import BLOCKED_MODULES, ISOLATION_FROM_UNWANTED_LIBRARIES


def _catch_invalid_data(
    data: typing.Any,
    validator: typing.Callable,
    logger
) -> None:
    with pytest.raises(ValueError):
        validator(data)
    logger.info(f'Invalid data "{data}" caught successfully')


def _check_for_validators(
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
            validators_found |= _check_for_validators(
                transpiled_schema=property_data,
                validators_to_check=validators_left,
            )
    return validators_found


@pytest.mark.order(1)
@pytest.mark.parametrize(
    'patch',
    consts.MOCK_SCHEMA_PATCHES,
)
def test_patched_schema_transpilation(
    patch: dict,
    mock_config_file: dict,
    logger
):
    logger.info('Testing schema transpilation for patch: %s', {
        property: patch[property]['type'] if 'type' in patch[property] else 'nested'
        for property in patch
    })
    transpiled_schema = Transpiler.schema(
        schema=mock_config_file | {
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
    validator_check_results = _check_for_validators(transpiled_schema, validators_to_check)

    assert all(
        result[0] is not None
        for result in validator_check_results.values()
    )

    for validator in validator_check_results.values():
        for sample in validator[1]:
            _catch_invalid_data(
                data=sample,
                validator=validator[0],  # type: ignore
                logger=logger
            )


@pytest.mark.order(2)
def test_merged_schema(
    mock_config_file,
    logger
):
    logger.info('Testing schema transpilation for schema merged from ALL previous patches')
    test_patched_schema_transpilation(
        patch=dict(
            ChainMap(*consts.MOCK_SCHEMA_PATCHES)
        ),
        mock_config_file=mock_config_file,
        logger=logger
    )


@pytest.mark.order(3)
@pytest.mark.parametrize(
    'blocked_module',
    BLOCKED_MODULES
)
def test_module_shadowing(
    blocked_module,
    mock_config_file,
    logger
):
    logger.info(ISOLATION_FROM_UNWANTED_LIBRARIES)
    try:
        Transpiler.supress_logging()
        forbidden_schema = Transpiler.schema(
            schema=mock_config_file | {
                'properties': {
                    'name': {
                        'description': 'Name of the test',
                        'type': 'str',
                        'validator': 'print(os)'
                    }
                }
            }
        )
        forbidden_schema(name='test')
    except ImportError as module_blocked:
        logger.info(f'Caught ImportError: {module_blocked} as expected')
        return
    pytest.fail(f'Didn\'t block module: {blocked_module}')
