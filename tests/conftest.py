import logging
import os
import pydoc
import typing

import pytest
import yaml

import consts
import phaistos.consts


def create_mock_schema_data(applied_properties: dict) -> dict:
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
        )] if 'validator' in property_data else []
        found_validators.extend(
            find_custom_validators(property_data.get('properties', {}))
        )
    return found_validators

@pytest.fixture(scope='session')
def mock_config_file() -> dict[str, typing.Any]:
    with open(
        file=os.path.join(consts.TESTS_ASSETS_PATH, 'mock.yaml'),
        mode='r',
        encoding='utf-8'
    ) as schema_file:
        return yaml.safe_load(schema_file)


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
