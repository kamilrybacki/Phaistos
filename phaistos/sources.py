"""
    Here, all validator function source snippets and templates are stored,
    to be then templated via simple string formatting and used in the compiler.

    The templates are:
    - FIELD_VALIDATOR_VALUE_COPY_TEMPLATE: A template to copy the value of a field to the global scope.
    - LOGGER_TEMPLATE: A template to create a logger in the global scope.
    - FIELD_VALIDATOR_FUNCTION_NAME_TEMPLATE: A template to create a field validator function name.
    - FIELD_VALIDATOR_FUNCTION_SOURCE_TEMPLATE: A template to create a field validator function.
    - MODEL_VALIDATOR_FUNCTION_NAME: The name of the model validator function.
    - MODEL_VALIDATOR_FUNCTION_SOURCE_TEMPLATE: A template to create a model validator function.
    - COLLECTION_VALIDATOR_TEMPLATE: A template to validate a collection type.

    The templates are used in the compiler to create the source code of the validator functions. The arguments passed to the validators are:
    - first_argument: The name of the first argument of the function (self or cls, depending which mode is used).
    - extra_arguments: Extra arguments that are passed to the function.
    - info: The info object that contains the field name and other information about the field (pydantic.ValidationInfo object with optional extra context)
"""

FIELD_VALIDATOR_VALUE_COPY_TEMPLATE = """
  globals()[info.field_name] = value
  locals()[info.field_name] = value
"""

LOGGER_TEMPLATE = """
  import logging
  globals()['logger'] = logging.getLogger('PHAISTOS (V)')
"""

FIELD_VALIDATOR_FUNCTION_NAME_TEMPLATE = '%s_validator'
FIELD_VALIDATOR_FUNCTION_SOURCE_TEMPLATE = f"""
%(decorator)s
def %(name)s(%(first_argument)s, value, %(extra_arguments)s info):
{LOGGER_TEMPLATE}
{FIELD_VALIDATOR_VALUE_COPY_TEMPLATE}
  if not value or value is None:
    raise ValueError('Value cannot be empty')
  %(source)s
  return value
"""

MODEL_VALIDATOR_FUNCTION_NAME = 'validate_model'
MODEL_VALIDATOR_FUNCTION_SOURCE_TEMPLATE = f"""
import typing
%(decorator)s
def %(name)s(%(first_argument)s, %(extra_arguments)s info):
{LOGGER_TEMPLATE}
  globals().update(info)
  locals().update(info)
  %(source)s
  return %(first_argument)s
"""

COLLECTION_VALIDATOR_TEMPLATE = """
for item in value:
  if not item:
    raise ValueError('Items in list cannot be empty')
  if not isinstance(item, %s):
    raise ValueError(f"Items in %s must be of type %s")
"""
