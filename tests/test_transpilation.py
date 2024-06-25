import typing

import pytest

import conftest
import consts

from phaistos.transpiler import Transpiler


def _catch_invalid_data(
    data: typing.Any,
    validator: typing.Callable,
    logger
) -> None:
    with pytest.raises(ValueError):
        validator(data)
    logger.info(f'Invalid data "{data}" caught successfully')


@pytest.mark.parametrize(
    'patch',
    consts.MOCK_SCHEMA_PATCHES
)
def test_patched_schema_transpilation(
    patch: dict,
    mock_config_file: dict,
    logger
):
    logger.info('Testing schema transpilation for patch: %s', {
        property: patch[property]['type']
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
    assert all(
        hasattr(transpiled_schema, validator[1])
        for validator in validators_to_check
    )

    for validator in validators_to_check:
        validator_method = getattr(transpiled_schema, validator[1])
        for sample in validator[2]:
            _catch_invalid_data(
                data=sample,
                validator=validator_method,
                logger=logger
            )
