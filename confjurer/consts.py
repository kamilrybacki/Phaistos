DEFAULT_INDENTATION = 2 * ' '

VALIDATOR_FUNCTION_TEMPLATE = f"""
def %s(cls, value):
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
