import logging
import os
import types

DEFAULT_INDENTATION = 2 * ' '

VALIDATOR_FUNCTION_NAME_TEMPLATE = '%s_validator'
VALIDATOR_FUNCTION_SOURCE_TEMPLATE = f"""
def %s(cls, value):
{DEFAULT_INDENTATION}if not value:
{DEFAULT_INDENTATION}{DEFAULT_INDENTATION}raise ValueError('Value cannot be empty')
{DEFAULT_INDENTATION}%s
{DEFAULT_INDENTATION}return value
"""

ALLOWED_COLLECTION_TYPES = {'list', 'set'}

COLLECTION_TYPE_REGEX = r'(?P<collection>\w+)\[(?P<item>\w+)\]'

COLLECTION_VALIDATOR_TEMPLATE = f"""
if not all(
{DEFAULT_INDENTATION}isinstance(item, %s)
{DEFAULT_INDENTATION}for item in value
):
{DEFAULT_INDENTATION}raise ValueError(f"Items in %s must be of type %s")
"""


def __setup_logger(logger_name: str) -> logging.Logger:
    new_logger = logging.getLogger(logger_name)
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


TRANSPILATION_LOGGER = __setup_logger('PHAISTOS (T)')

DISCOVERY_EXCEPTIONS = {
    FileNotFoundError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH points to a non-existent directory',
    NotADirectoryError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH points to a file',
    PermissionError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH is not accessible',
    KeyError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH not set'
}

# This is a list of modules that should not be available to the user
# when they are writing validators, so they are shadowed by fake modules
# with the same name and then inserted into the globals of the validator
# function during compilation

BLOCKED_MODULES = ['os', 'sys', 'importlib', 'pydoc', 'subprocess', 'pickle', 'shutil', 'tempfile', 'inspect', 'shlex']

with open('/tmp/null_module.py', 'w', encoding='utf-8') as null_module:
    null_module.writelines([
        'def __getattr__(*args):\n',
        '\traise ImportError("Blocked module")\n',
        'def __setattr__(*args):\n',
        '\traise ImportError("Blocked module")\n',
    ])

NULL_MODULE = types.ModuleType('BLOCKED')
NULL_MODULE.__file__ = '/tmp/__init__.py'

ISOLATION_FROM_UNWANTED_LIBRARIES = {
    module_name: NULL_MODULE
    for module_name in BLOCKED_MODULES
} if bool(
    os.environ.get('PHAISTOS__ENABLE_UNSAFE_VALIDATORS', 'False')
) else {}
