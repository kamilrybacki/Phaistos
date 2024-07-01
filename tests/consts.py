from __future__ import annotations
import os
import random
import typing

import phaistos.typings

TESTS_ASSETS_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets'
)
RANDOM_DATA = ''.join(str(random.randint(0, 9)) for _ in range(10))


class MockRawSchemaProperty(phaistos.typings.RawSchemaProperty):
    invalid: typing.NotRequired[list[typing.Any]]
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
            'validator': "import string\nif set(value).difference(string.ascii_letters+string.digits): raise ValueError('Name contains special characters')",
            'invalid': [
                'na$!',
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

SCHEMA_DISCOVERY_FAIL_CASES: list[
    tuple[str, type[Exception]]
] = [
    (
        """
        os.environ['PHAISTOS__SCHEMA_PATH'] = '/invalid/path'
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
        os.environ['PHAISTOS__SCHEMA_PATH'] = test_file_path
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
        os.environ['PHAISTOS__SCHEMA_PATH'] = test_dir_path
        """,
        PermissionError,
    ),
    (
        """
        del os.environ['PHAISTOS__SCHEMA_PATH']
        """,
        KeyError,
    )
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
    }
]
