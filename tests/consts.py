from __future__ import annotations
import os
import random
import typing

import phaistos.consts
import phaistos.typings

TESTS_ASSETS_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets'
)
RANDOM_DATA = ''.join(str(random.randint(0, 9)) for _ in range(10))


class MockRawSchemaProperty(phaistos.typings.RawSchemaProperty):
    invalid: typing.NotRequired[tuple[list, list]]
    properties: typing.NotRequired[dict[str, MockRawSchemaProperty]]  # type: ignore


MOCK_SCHEMA_PATCHES: list[
    dict[str, MockRawSchemaProperty]
] = [
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
        }
    },
    {
        'income': {
            'description': 'Income of the test',
            'type': 'float',
            'validator': {
                "mode": "after",
                "source": "if value < 1000.0: raise ValueError('Income must be more than 1000.0')"
            },
            'invalid': ([
                999.99,
                0.0,
                None
            ], [])
        },
        'label': {
            'description': 'Name of the test',
            'type': 'str',
            'validator': {
                "mode": "after",
                "source": "import string\nif set(value).difference(string.ascii_letters+string.digits): raise ValueError('Name contains special characters')"
            },
            'invalid': ([
                'na$!',
                '',
                None
            ], [])
        },
        'tags': {
            'description': 'Tags for the test',
            'type': 'list[str]',
            'validator': {
                "mode": "after",
                "source": "if len(value) < 2: raise ValueError('Tags must have at least 2 items')"
            },
            'invalid': ([
                ['t1'],
                [None, None, None]
            ], [])
        }
    },
    {
        'numbers': {
            'description': 'Numbers for the test',
            'type': 'list[int]',
            'constraints': {
                'min_items': 2
            },
            'invalid': ([], [[0]])
        },
        'name': {
            'description': 'Name of the test',
            'type': 'str',
            'constraints': {
                'min_length': 2
            },
            'invalid': ([], ['a'])
        },
        'age': {
            'description': 'Age of the test',
            'type': 'int',
            'constraints': {
                'ge': 0,
                'le': 100
            },
            'invalid': ([], [999])
        }
    },
    {
        'rank': {
            'description': 'Rank of the test',
            'type': 'int',
            'constraints': {
                'le': 10
            },
            'validator': {
                "mode": "after",
                "source": "if value < 1:  raise ValueError('Rank must be between 1 and 10')"
            },
            'invalid': ([
                0,
                None
            ], [
                11
            ])
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
                'nested_age': {
                    'description': 'Age of the nested test',
                    'type': 'int',
                    'invalid': ([], [
                        0,
                        -1,
                        None
                    ])
                },
            }
        }
    },
]

SCHEMA_DISCOVERY_FAIL_CASES: list[
    tuple[str, type[Exception]]
] = [
    (
        """
        cls._current_schemas_path = '/invalid/path'
        """,
        FileNotFoundError,
    ),
    (
        """
        test_file_path = '/tmp/phaistos_test_file'
        try:
            os.remove(test_file_path)
        except FileNotFoundError:
            pass
        open(test_file_path, 'w').close()
        cls._current_schemas_path = test_file_path
        """,
        NotADirectoryError,
    ),
    (
        """
        test_dir_path = '/tmp/phaistos_test_dir'
        try:
            os.mkdir(test_dir_path)
        except FileExistsError:
            pass
        os.chmod(test_dir_path, 0o04111)
        cls._current_schemas_path = test_dir_path
        """,
        PermissionError,
    ),
]

# Inspired by: https://supakeen.com/weblog/dangers-in-pythons-standard-library.html

VULNERABILITIES_TO_TEST = [
    {
        'name': 'FS peek',
        'code': 'print(os.listdir("/"))'
    },
    {
        'name': 'Messing up envvars',
        'code': 'os.environ["PATH"]="/dev/null"'
    },
    {
        'name': 'RCE via Pickle',
        'code': 'pickle.loads(b"\\x80\\x03cbuiltins\\nprint\\nq\\x00X\\x05\\x00\\x00\\x00helloq\\x01\\x85q\\x02Rq\\x03.")'
    },
    {
        'name': 'Shlex with subprocess',
        'code': 'subprocess.check_output("echo {}".format(shlex.split("foo;echo${IFS}hello")[0]))'
    },
    {
        'name': "Removal via shutil",
        'code': 'shutil.rmtree("/tmp", ignore_errors=False)'
    },
    *[
        {
            'name': f'Importing {module_name}',
            'code': f'import {module_name}'
        }
        for module_name in phaistos.consts.BLOCKED_MODULES
    ],
    *[
        {
            'name': f'Accessing {module_name} attributes',
            'code': f'{module_name}.LOCK'
        }
        for module_name in phaistos.consts.BLOCKED_MODULES
    ]
]
