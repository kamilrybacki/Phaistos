import pydoc
import random

import pytest

import confjurer.transpile


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


@pytest.mark.parametrize(
    'patch',
    [
        {
            'version': '0.1.0',
            'properties': {
                'name': {
                    'description': 'Name of the test',
                    'type': 'str',
                    'default': f'default-{RANDOM_DATA}'
                },
                'age': {
                    'description': 'Age of the test',
                    'type': 'int',
                },
                'value': {
                    'description': 'Value of the test',
                    'type': 'float',
                },
            }
        }
    ]
)
def test_valid_schema_transpilation(
    patch: dict,
    mock_config_file: dict
):
    transpiled_schema = confjurer.utils.transpile.transpile_schema(
        schema=mock_config_file | patch
    )
    mock_schema_test_data = _create_mock_schema_data(
        applied_properties=patch['properties']
    )
    assert transpiled_schema.model_validate(mock_schema_test_data)
