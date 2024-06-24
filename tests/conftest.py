import os
import typing

import pytest
import yaml


TESTS_ASSETS_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets'
)


@pytest.fixture(scope='session')
def mock_config_file() -> dict[str, typing.Any]:
    with open(
        file=os.path.join(TESTS_ASSETS_PATH, 'mock.yaml'),
        mode='r',
        encoding='utf-8'
    ) as schema_file:
        return yaml.safe_load(schema_file)
