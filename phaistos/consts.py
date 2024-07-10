import os
import types

import phaistos.utils

TRANSPILATION_LOGGER = phaistos.utils.setup_logger('PHAISTOS (T)')
VALIDATION_LOGGER = phaistos.utils.setup_logger('PHAISTOS (V)')
COMPILATION_LOGGER = phaistos.utils.setup_logger('PHAISTOS (C)')

ALLOWED_COLLECTION_TYPES = {'list', 'set'}

COLLECTION_TYPE_REGEX = r'(?P<collection>\w+)\[(?P<item>\w+)\]'

# This is a list of modules that should not be available to the user
# when they are writing validators, so they are shadowed by fake modules
# with the same name and then inserted into the globals of the validator
# function during compilation
BLOCKED_MODULES = ['os', 'sys', 'importlib', 'pydoc', 'subprocess', 'pickle', 'shutil', 'tempfile', 'inspect', 'shlex']

NULL_MODULE = types.ModuleType('BLOCKED')
setattr(NULL_MODULE, 'LOCK', True)
setattr(NULL_MODULE, '__getattr__', phaistos.utils.block)

ISOLATION_FROM_UNWANTED_LIBRARIES = {
    module_name: NULL_MODULE
    for module_name in BLOCKED_MODULES
} if bool(
    os.environ.get('PHAISTOS__ENABLE_UNSAFE_VALIDATORS', 'False')
) else {}

DISCOVERY_EXCEPTIONS = {
    FileNotFoundError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH points to a non-existent directory',
    NotADirectoryError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH points to a file',
    PermissionError: 'Error while discovering schemas: PHAISTOS__SCHEMA_PATH is not accessible',
}
