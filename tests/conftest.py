import contextlib
import logging
import os
import pydoc
import typing

import pytest
import yaml

import consts  # type: ignore
import phaistos.consts
import phaistos.typings


def create_mock_schema_data(applied_properties: dict[str, phaistos.typings.RawSchemaProperty]) -> dict[str, typing.Any]:
    data = {}
    for property_name, property_data in applied_properties.items():
        if 'default' in property_data:
            data[property_name] = property_data['default']
        elif 'type' in property_data:
            data[property_name] = pydoc.locate(property_data['type'])(consts.RANDOM_DATA)  # type: ignore
        elif 'properties' in property_data:
            data[property_name] = create_mock_schema_data(property_data['properties'])
        else:
            raise ValueError(f'Invalid property data: {property_data}')
    return data


def find_custom_validators(data: dict) -> list[tuple[str, str, list]]:
    found_validators = []
    for property_name, property_data in data.items():
        found_validators += [(
            property_data['type'],
            phaistos.consts.VALIDATOR_FUNCTION_NAME_TEMPLATE % property_name,
            property_data['invalid']
        )] if 'validators' in property_data else []
        found_validators.extend(
            find_custom_validators(property_data.get('properties', {}))
        )
    return found_validators


def __open_yaml_file(file_path: str) -> phaistos.typings.SchemaInputFile:
    with open(
        file=file_path,
        mode='r',
        encoding='utf-8'
    ) as schema_file:
        return yaml.safe_load(schema_file)


@pytest.fixture(scope='session')
def mock_config_file_base() -> phaistos.typings.SchemaInputFile:
    return __open_yaml_file(
        os.path.join(consts.TESTS_ASSETS_PATH, 'mock.yaml')
    )


@pytest.fixture(scope='session')
def faulty_config_file() -> phaistos.typings.SchemaInputFile:
    return __open_yaml_file(
        os.path.join(consts.TESTS_ASSETS_PATH, 'faulty.yaml')
    )


@pytest.fixture(scope='session')
def valid_config_file() -> phaistos.typings.SchemaInputFile:
    return __open_yaml_file(
        os.path.join(consts.TESTS_ASSETS_PATH, 'valid.yaml')
    )


@pytest.fixture(scope='session')
def logger() -> logging.Logger:
    new_logger = logging.getLogger('PHAISTOS (TESTS)')
    new_logger.propagate = False
    new_logger.handlers.clear()
    log_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    new_logger.addHandler(log_handler)
    new_logger.setLevel(logging.DEBUG)
    return new_logger


def toggle_schema_discovery(state: bool) -> None:
    if state:
        with contextlib.suppress(KeyError):
            del os.environ['PHAISTOS__DISABLE_SCHEMA_DISCOVERY']
    else:
        os.environ['PHAISTOS__DISABLE_SCHEMA_DISCOVERY'] = '1'


@contextlib.contextmanager
def schema_discovery(state: bool = True) -> typing.Generator[None, None, None]:
    toggle_schema_discovery(state)
    yield
    toggle_schema_discovery(not state)
