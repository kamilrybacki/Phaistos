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
import phaistos.schema
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
@pytest.mark.order(1)
def test_schema_discovery_exceptions(
    hot_patch: str,
    exception: type[Exception],
    logger,
    monkeypatch,
) -> None:
    logger.info(f'Testing schema discovery exception: {exception.__name__}')

    os.environ['PHAISTOS__SCHEMA_PATH'] = consts.TESTS_ASSETS_PATH

    original_get_available_schemas = copy.deepcopy(
        phaistos.Manager.get_available_schemas
    )

    def patched_get_available_schemas():
        patch_function = types.FunctionType(
            compile(
                textwrap.dedent(hot_patch),
                '',
                'exec'
            ),
            globals={
                **globals(),
                'cls': phaistos.Manager
            }
        )
        patch_function()  # pylint: disable=not-callable
        return original_get_available_schemas()

    monkeypatch.setattr(
        phaistos.Manager,
        'get_available_schemas',
        patched_get_available_schemas
    )

    with pytest.raises(exception):
        phaistos.Manager.start(discover=True)
    logger.info(f'Successfully tested schema discovery exception: {exception.__name__}')


@pytest.mark.order(2)
def test_schema_discovery_disabled(logger) -> None:
    logger.info('Testing schema discovery disabled')
    manager = phaistos.Manager.start(discover=False)
    assert not manager._schemas  # pylint: disable=protected-access


@pytest.mark.order(3)
def test_manual_path_specification(logger) -> None:
    logger.info(f'Pointing to {consts.TESTS_ASSETS_PATH} manually')
    original_path = os.environ.get('PHAISTOS__SCHEMA_PATH', '')
    manager = phaistos.Manager.start(
        schemas_path=consts.TESTS_ASSETS_PATH
    )
    assert manager._current_schemas_path == consts.TESTS_ASSETS_PATH  # pylint: disable=protected-access
    assert not manager._schemas  # pylint: disable=protected-access
    os.environ['PHAISTOS__SCHEMA_PATH'] = original_path


@pytest.mark.order(4)
def test_manual_schema_loading() -> None:
    with conftest.schema_discovery(state=False):
        manager = phaistos.Manager.start()

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
        manager.load_schema(schema)

        # Validate the data against the schema
        assert manager.validate(**MOCK_PERSON).valid  # type: ignore


@pytest.mark.parametrize(
    'config_filename',
    [
        'valid_config_file',
        'faulty_flat_config_file',
        'faulty_nested_config_file',
        'faulty_double_nested_config_file',
    ],
)
@pytest.mark.order(5)
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

        manager: phaistos.Manager = phaistos.Manager.start()
        results = manager.validate(
            data=data_from_schema,
            schema=manager.load_schema(config_file)
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
        del manager

    os.environ['PHAISTOS__SCHEMA_PATH'] = initial_schema_path


@pytest.mark.order(6)
def test_if_context_is_passed_during_validation() -> None:
    with conftest.schema_discovery(state=False):
        manager = phaistos.Manager.start()

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
        manager.load_schema(schema)

        # Validate data against the schema with doomed manager (it will always raise an error, because value in context is the main culprit)
        assert not manager.validate(**MOCK_PERSON).valid  # type: ignore


@pytest.mark.order(7)
def test_repeated_validations(faulty_flat_config_file) -> None:
    with conftest.schema_discovery(state=False):
        manager = phaistos.Manager.start()
        schema_name = manager.load_schema(faulty_flat_config_file)
        mock_data = conftest.create_mock_schema_data(faulty_flat_config_file['properties'])

        first_validation = manager.validate(data=mock_data, schema=schema_name)
        assert not first_validation.valid  # type: ignore

        number_of_errors = len(first_validation.errors)

        second_validation = manager.validate(data=mock_data, schema=schema_name)
        assert not second_validation.valid  # type: ignore
        assert len(second_validation.errors) == number_of_errors


@pytest.mark.order(8)
def test_constructor_call_for_model(faulty_flat_config_file) -> None:
    with conftest.schema_discovery(state=False):
        manager = phaistos.Manager.start()
        schema_name = manager.load_schema(faulty_flat_config_file)
        mock_data = conftest.create_mock_schema_data(faulty_flat_config_file['properties'])

        model = manager.get_factory(schema_name)
        assert model.build(mock_data) is None
        assert model._model.validation_errors != []  # pylint: disable=protected-access
