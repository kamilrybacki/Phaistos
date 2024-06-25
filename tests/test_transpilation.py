import pytest

from conftest import RANDOM_DATA, _create_mock_schema_data

from phaistos.transpiler import Transpiler


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
                'is_active': {
                    'description': 'Is the test active',
                    'type': 'bool',
                },
                'tags': {
                    'description': 'Tags for the test',
                    'type': 'list[str]',
                    'validator': "if len(value) < 2: raise ValueError('Tags must have at least 2 items')",
                },
            }
        }
    ]
)
def test_valid_schema_transpilation(
    patch: dict,
    mock_config_file: dict
):
    transpiled_schema = Transpiler.schema(
        schema=mock_config_file | patch
    )
    mock_schema_test_data = _create_mock_schema_data(
        applied_properties=patch['properties']
    )
    print(mock_schema_test_data)
    assert transpiled_schema.model_validate(mock_schema_test_data)
