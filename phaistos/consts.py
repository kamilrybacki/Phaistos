import logging
import os
import types

import phaistos.exceptions


def _block(*args, **kwargs):
    raise phaistos.exceptions.ForbiddenModuleUseInValidator()


ALLOWED_COLLECTION_TYPES = {'list', 'set'}

COLLECTION_TYPE_REGEX = r'(?P<collection>\w+)\[(?P<item>\w+)\]'

BLOCKED_MODULES = ['os', 'sys', 'importlib', 'pydoc', 'subprocess', 'pickle', 'shutil', 'tempfile', 'inspect', 'shlex']

NULL_MODULE = types.ModuleType('BLOCKED')
setattr(NULL_MODULE, 'LOCK', True)
setattr(NULL_MODULE, '__getattr__', _block)

ISOLATION_FROM_UNWANTED_LIBRARIES = {
    module_name: NULL_MODULE
    for module_name in BLOCKED_MODULES
} if bool(
    os.environ.get('PHAISTOS__ENABLE_UNSAFE_VALIDATORS', 'False')
) else {}


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
VALIDATION_LOGGER = __setup_logger('PHAISTOS (V)')

DISCOVERY_EXCEPTIONS = {
    FileNotFoundError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH points to a non-existent directory',
    NotADirectoryError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH points to a file',
    PermissionError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH is not accessible',
}

# This is a list of modules that should not be available to the user
# when they are writing validators, so they are shadowed by fake modules
# with the same name and then inserted into the globals of the validator
# function during compilation
