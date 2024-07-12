import os
import logging
import typing

import phaistos  # type: ignore
import phaistos.typings  # type: ignore

SCHEMA_TO_USE: phaistos.typings.SchemaInputFile = {
    'version': '0.1.0',
    'name': 'Mockument',
    'description': 'A mockk entry',
    'properties': {
        'name': {
            'type': 'str',
            'description': 'The name of the mockument',
            'validator': "if not value[0].isupper(): raise ValueError('The name must start with an uppercase letter')"
        },
        'year': {
            'type': 'int',
            'description': 'The year the mockument was released',
            'validator': "import datetime\nif value > datetime.datetime.now().year: raise ValueError('The year must be in the past')"
        },
        'rating': {
            'type': 'int',
            'description': 'The rating of the mockument',
            'constraints': {
                'le': 10,
                'ge': 1
            },
        }
    }
}

GOOD_MOCKUMENT = {
    'name': 'This is a mockument',
    'year': 2021,
    'rating': 5
}

BAD_MOCKUMENT = {
    'name': 'this is a mockument',
    'year': 2022,
    'rating': 11
}


def validate_mockument_data(
    initialized_manager: phaistos.Manager,
    data: typing.Any,
    name: str
) -> None:
    logging.info(f'Validating data {data} against schema: {name}')
    result = initialized_manager.validate(data, name)
    logging.info('Validation result:')
    logging.info(result)


if __name__ == '__main__':
    # Disable schema discovery by setting the environment variable
    os.environ['PHAISTOS__DISABLE_SCHEMA_DISCOVERY'] = '1'

    manager = phaistos.Manager.start()
    schema_id = manager.load_schema(SCHEMA_TO_USE)
    logging.info(f'Loaded schema with ID: {schema_id}')

    for example_data in [
        GOOD_MOCKUMENT,
        BAD_MOCKUMENT
    ]:
        validate_mockument_data(manager, example_data, schema_id)

    # Clean up the environment variable
    del os.environ['PHAISTOS__DISABLE_SCHEMA_DISCOVERY']
