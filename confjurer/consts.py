INDENTATION = 2 * ' '

VALIDATOR_FUNCTION_TEMPLATE = f"""
def %s(cls, value):
{INDENTATION}%s
{INDENTATION}return value
"""
