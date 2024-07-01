# pylint: disable=wrong-import-position
import copy
import os
import shutil
import textwrap
import types
import yaml

import pytest

import consts  # type: ignore
import conftest  # type: ignore

import phaistos
import phaistos.consts
from phaistos.typings import SchemaInputFile


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
) -> None:
    logger.info(f'Testing schema discovery exception: {exception.__name__}')

    original_get_available_schemas = copy.deepcopy(
        phaistos.Validator.get_available_schemas  # pylint: disable=protected-access
    )

    original_schema_path = copy.deepcopy(
        os.environ.get('PHAISTOS__SCHEMA_PATH', '')
    )

    def patched_get_available_schemas(self: phaistos.Validator, path: str = ''):
        patch_function = types.FunctionType(
            compile(
                textwrap.dedent(hot_patch),
                '',
                'exec'
            ),
            globals=globals()
        )
        patch_function()  # pylint: disable=not-callable
        return original_get_available_schemas(self, path)

    monkeypatch.setattr(
        phaistos.Validator,
        'get_available_schemas',
        patched_get_available_schemas
    )

    with pytest.raises(exception):
        phaistos.Validator.start()
    logger.info(f'Successfully tested schema discovery exception: {exception.__name__}')
    os.environ['PHAISTOS__SCHEMA_PATH'] = original_schema_path


def _run_data_validation(
    schema: SchemaInputFile,
    validator: phaistos.Validator,
    logger
) -> None:
    data_from_schema = conftest.create_mock_schema_data(
        applied_properties=schema['properties']
    )

    logger.info(f'Validating data {data_from_schema} against schema: {schema["name"]}')

    results = validator.against_schema(
        data=data_from_schema,
        schema=schema['name']
    )

    logger.info(f'Validation results:\n{results}')

    assert results.valid == schema['_valid']  # type: ignore
    del validator


def test_schema_validation_workflow(faulty_config_file, valid_config_file, logger) -> None:
    temporary_schema_directory = '/tmp/phaistos_test_configs'
    shutil.rmtree(temporary_schema_directory, ignore_errors=True)
    os.makedirs(temporary_schema_directory, exist_ok=True)

    for config_file in [
        faulty_config_file,
        valid_config_file
    ]:
        temporary_schema_name = f'mock-{config_file["name"]}-{config_file["version"]}.yaml'
        with open(
            file=f'{temporary_schema_directory}/{temporary_schema_name}',
            mode='w',
            encoding='utf-8'
        ) as schema_file:
            yaml.dump(config_file, schema_file)
        logger.info(f'Created temporary schema: {temporary_schema_name}')

    initial_schema_path = os.environ.get('PHAISTOS__SCHEMA_PATH', '')
    os.environ['PHAISTOS__SCHEMA_PATH'] = temporary_schema_directory

    with conftest.schema_discovery():
        validator: phaistos.Validator = phaistos.Validator.start()
        for schema in [faulty_config_file, valid_config_file]:
            _run_data_validation(schema, validator, logger)

    os.environ['PHAISTOS__SCHEMA_PATH'] = initial_schema_path
