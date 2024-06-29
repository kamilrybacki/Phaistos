# pylint: disable=wrong-import-position
import copy
import os
import textwrap
import types
import yaml

import pytest

import consts  # type: ignore
import conftest  # type: ignore

import phaistos
import phaistos.consts


@pytest.mark.parametrize(
    'hot_patch, exception',
    consts.SCHEMA_DISCOVERY_FAIL_CASES,
    ids=[
        exception.__name__
        for _, exception in consts.SCHEMA_DISCOVERY_FAIL_CASES
    ]
)
def test_schema_discovery_exceptions(
    hot_patch: str,
    exception: type[Exception],
    logger,
    monkeypatch
):
    logger.info(f'Testing schema discovery exception: {exception.__name__}')

    original_get_available_schemas = copy.deepcopy(
        phaistos.Validator.get_available_schemas  # pylint: disable=protected-access
    )

    original_schema_path = copy.deepcopy(
        os.environ.get('PHAISTOS__SCHEMA_PATH', '')
    )

    def patched_get_available_schemas():
        patch_function = types.FunctionType(
            compile(
                textwrap.dedent(hot_patch),
                '',
                'exec'
            ),
            globals=globals()
        )
        patch_function()  # pylint: disable=not-callable
        return original_get_available_schemas()

    monkeypatch.setattr(
        phaistos.Validator,
        'get_available_schemas',
        patched_get_available_schemas
    )

    with pytest.raises(exception):
        phaistos.Validator.get_available_schemas()  # pylint: disable=protected-access
    logger.info(f'Successfully tested schema discovery exception: {exception.__name__}')
    os.environ['PHAISTOS__SCHEMA_PATH'] = original_schema_path


def test_full_schema_validation(faulty_config_file):
    temporary_schema_directory = f'/tmp/{faulty_config_file["name"]}'
    os.makedirs(temporary_schema_directory, exist_ok=True)

    temporary_schema_name = f'mock-{faulty_config_file["version"]}.yaml'

    with open(
        file=f'{temporary_schema_directory}/{temporary_schema_name}',
        mode='w',
        encoding='utf-8'
    ) as schema_file:
        yaml.dump(
            faulty_config_file,
            schema_file
        )

    initial_schema_path = os.environ.get('PHAISTOS__SCHEMA_PATH', '')
    with conftest.schema_discovery():
        os.environ['PHAISTOS__SCHEMA_PATH'] = temporary_schema_directory

        validator = phaistos.Validator.start()

        data_from_schema = conftest.create_mock_schema_data(
            applied_properties=faulty_config_file['properties']
        )

        validator.against_schema(
            data=data_from_schema,
            schema=faulty_config_file['name']
        )

        os.environ['PHAISTOS__SCHEMA_PATH'] = initial_schema_path
