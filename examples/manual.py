import datetime
import logging
import os

import pydantic

import phaistos


EXAMPLE_MOCKUMENTS = {
    'valid': {
        'name': 'The Room',
        'year': 2003,
        'rating': 3.7
    },
    'invalid': {
        'name': 'Troll 2',
        'year': datetime.datetime.now().year + 1,
        'rating': 10000
    },
}


def compile_manually():
    validator = phaistos.Validator.start()

    # Get the Mockument data model
    mockument = validator.get_model('Mockument')

    # Create the valid mockument entry
    valid_mockument = mockument(
        **EXAMPLE_MOCKUMENTS['valid']
    )

    # Show the valid mockument entry
    logging.info(valid_mockument)

    # Create the invalid mockument entry
    try:
        _ = mockument(
            **EXAMPLE_MOCKUMENTS['invalid']
        )
    except pydantic.ValidationError as wrong_data:
        logging.error(f'Invalid mockument data: {wrong_data}')


if __name__ == '__main__':
    example_schemas_path = os.path.join(os.path.dirname(__file__), 'schemas')
    os.environ['PHAISTOS__SCHEMA_PATH'] = example_schemas_path
    compile_manually()
