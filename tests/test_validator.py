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


MOCK_PERSON = {
    'data': {
        "name": "John Doe",
        "age": 30,
        "email": "xxx@gmail.com"
    },
    'schema': 'Person'
}


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


def test_manual_schema_loading() -> None:
    with conftest.schema_discovery(state=False):
        validator = phaistos.Validator.start()

        schema: SchemaInputFile = {
            "version": "v1",
            "description": "A schema for a person",
            "name": "Person",
            "properties": {
                "age": {
                    "type": "int",
                    "description": "The age of the person",
                    "validator": {
                        "mode": "after",
                        "source": "if value < 18: raise ValueError('The age must be at least 18')"
                    }
                }
            }
        }

        # Load the schema
        validator.load_schema(schema)

        # Validate the data against the schema
        assert validator.validate(**MOCK_PERSON).valid  # type: ignore


@pytest.mark.parametrize(
    'config_filename',
    [
        'valid_config_file',
        'faulty_flat_config_file',
        'faulty_nested_config_file',
        'faulty_double_nested_config_file',
    ],
)
def test_schema_validation_workflow(config_filename: str, logger, request) -> None:
    config_file = request.getfixturevalue(config_filename)
    temporary_schema_directory = '/tmp/phaistos_test_configs'
    shutil.rmtree(temporary_schema_directory, ignore_errors=True)
    os.makedirs(temporary_schema_directory, exist_ok=True)

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

    with conftest.schema_discovery(state=False):
        data_from_schema = conftest.create_mock_schema_data(
            applied_properties=config_file['properties']
        )

        validator: phaistos.Validator = phaistos.Validator.start()
        results = validator.validate(
            data=data_from_schema,
            schema=validator.load_schema(config_file)
        )

        logger.info(f'Validation results:\n{results}')

        assert results.valid == config_file['_valid']  # type: ignore
        if not results.valid:
            failed_fields = [
                error.name
                for error in results.errors
            ]
            difference = set(failed_fields) ^ set(config_file['_expected_failures'])
            assert not difference, f'Failed fields: {failed_fields}'
        del validator

    os.environ['PHAISTOS__SCHEMA_PATH'] = initial_schema_path


def test_if_context_is_passed_during_validation() -> None:
    with conftest.schema_discovery(state=False):
        validator = phaistos.Validator.start()

        schema: SchemaInputFile = {
            "version": "v1",
            "description": "A schema for a person",
            "name": "Person",
            "properties": {
                "age": {
                    "type": "int",
                    "description": "The age of the person",
                    "validator": {
                        "mode": "after",
                        "source": "if info.context.get('fail'): raise ValueError('I was destined for failure :(')"
                    }
                }
            },
            "context": {
                "fail": True
            }
        }

        # Load the schema
        validator.load_schema(schema)

        # Validate data against the schema with doomed validator (it will always raise an error, because value in context is the main culprit)
        assert not validator.validate(**MOCK_PERSON).valid  # type: ignore
