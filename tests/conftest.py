import os
import pydoc
import random
import typing

import pytest
import yaml


TESTS_ASSETS_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets'
)
RANDOM_DATA = ''.join(str(random.randint(0, 9)) for _ in range(10))


def _create_mock_schema_data(applied_properties: dict) -> dict:
    data = {}
    for property_name, property_data in applied_properties.items():
        if 'default' in property_data:
            data[property_name] = property_data['default']
        elif 'type' in property_data:
            data[property_name] = pydoc.locate(property_data['type'])(RANDOM_DATA)  # type: ignore
        elif 'properties' in property_data:
            data[property_name] = _create_mock_schema_data(property_data['properties'])
        else:
            raise ValueError(f'Invalid property data: {property_data}')
    return data


@pytest.fixture(scope='session')
def mock_config_file() -> dict[str, typing.Any]:
    with open(
        file=os.path.join(TESTS_ASSETS_PATH, 'mock.yaml'),
        mode='r',
        encoding='utf-8'
    ) as schema_file:
        return yaml.safe_load(schema_file)
