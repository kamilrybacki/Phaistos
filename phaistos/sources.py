MODEL_ALL_FIELDS_COPY_TEMPLATE = """
  for field in %(first_argument)s.__dict__:
    globals()[field] = getattr(%(first_argument)s, field)
"""

FIELD_VALIDATOR_VALUE_COPY_TEMPLATE = """
  globals()[info.field_name] = value
"""

LOGGER_TEMPLATE = """
  import logging
  globals()['logger'] = logging.getLogger('PHAISTOS (V)')
"""

FIELD_VALIDATOR_FUNCTION_NAME_TEMPLATE = '%s_validator'
FIELD_VALIDATOR_FUNCTION_SOURCE_TEMPLATE = f"""
%(decorator)s
def %(name)s(%(first_argument)s, value, %(extra_arguments)s info: pydantic.ValidationInfo):
{LOGGER_TEMPLATE}
{FIELD_VALIDATOR_VALUE_COPY_TEMPLATE}
  if not value or value is None:
    raise ValueError('Value cannot be empty')
  %(source)s
  return value
"""

MODEL_VALIDATOR_FUNCTION_NAME = 'validate_model'
MODEL_VALIDATOR_FUNCTION_SOURCE_TEMPLATE = f"""
%(decorator)s
def %(name)s(%(first_argument)s, %(extra_arguments)s info: pydantic.ValidationInfo):
{LOGGER_TEMPLATE}
{MODEL_ALL_FIELDS_COPY_TEMPLATE}
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
