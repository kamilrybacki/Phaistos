import datetime
import logging
import os

import pydantic

import phaistos  # type: ignore


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


def test_model_instances_creation():
    manager = phaistos.Manager.start()

    # Get the Mockument data model
    mockument_factory = manager.get_factory('Mockument')

    # Create the valid mockument entry
    valid_mockument = mockument_factory.build(
        EXAMPLE_MOCKUMENTS['valid']
    )

    # Show the valid mockument entry
    logging.info(valid_mockument)

    # Create the invalid mockument entry
    try:
        _ = mockument_factory.build(
            EXAMPLE_MOCKUMENTS['invalid']
        )
    except pydantic.ValidationError as wrong_data:
        logging.error(f'Invalid mockument data: {wrong_data}')


if __name__ == '__main__':
    example_schemas_path = os.path.join(os.path.dirname(__file__), 'schemas')
    os.environ['PHAISTOS__SCHEMA_PATH'] = example_schemas_path
    test_model_instances_creation()
