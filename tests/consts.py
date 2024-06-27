import os
import random

from phaistos.consts import DISCOVERY_EXCEPTIONS

TESTS_ASSETS_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets'
)
RANDOM_DATA = ''.join(str(random.randint(0, 9)) for _ in range(10))

MOCK_SCHEMA_PATCHES = [
    {
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
            'invalid': [
                ['tag1'],
                [None, None, None]
            ]
        },
    },
    {
        'income': {
            'description': 'Income of the test',
            'type': 'float',
            'validator': "if value < 1000.0: raise ValueError('Income must be more than 1000.0')",
            'invalid': [
                999.99,
                0.0,
                None
            ]
        },
        'label': {
            'description': 'Name of the test',
            'type': 'str',
            'validator': "if not value[0].isupper(): raise ValueError('Name must start with an uppercase letter')",
            'invalid': [
                'name',
                '',
                None
            ]
        },
    },
    {
        'nested': {
            'description': 'Nested property',
            'properties': {
                'nested_name': {
                    'description': 'Name of the nested test',
                    'type': 'str',
                },
                'age_name': {
                    'description': 'Age of the nested test',
                    'type': 'int',
                    'validator': "if value < 18: raise ValueError('Age must be more than 18')",
                    'invalid': [
                        17,
                        0,
                        None
                    ]
                },
            }
        }
    }
]

SCHEMA_DISCOVERY_FAIL_CASES = [
    (
        """
        os.environ['PHAISTOS__SCHEMA_PATH'] = '/invalid/path'
        """,
        FileNotFoundError,
    ),
    (
        """
        os.remove('/tmp/phaistos_test_file')
        open('/tmp/phaistos_test_file', 'w').close()
        os.environ['PHAISTOS__SCHEMA_PATH'] = '/tmp/phaistos_test_file'
        """,
        NotADirectoryError,
    ),
    (
        """
        os.environ['PHAISTOS__SCHEMA_PATH'] = '/etc/passwd'
        """,
        PermissionError,
    ),
    (
        """

        """,
        KeyError,
    )
]
