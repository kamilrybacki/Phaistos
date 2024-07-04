import datetime
import dataclasses
import logging
import os

import phaistos


@dataclasses.dataclass
class Mockument:
    """
    Mockument is a dataclass representing a mockumentary movie.
    """
    name: str
    year: int
    rating: float

    def __post_init__(self):
        if self.year > datetime.datetime.now().year:
            raise ValueError('Year cannot be in the future')
        if self.rating > 10:
            raise ValueError('Rating cannot be higher than 10')
        if self.rating < 0:
            raise ValueError('Rating cannot be lower than 0')


@dataclasses.dataclass
class JustPretendItsADatabase:
    """
    JustPretendItsADatabase is a dataclass representing a database that stores mockumentary movies.

    It requires a configuration to be passed in the form of a dictionary with 'login' and 'password' keys.
    """
    config: dict = dataclasses.field(default_factory=dict)
    _data: dict = dataclasses.field(default_factory=dict)
    _logged: bool = dataclasses.field(init=False, default=False)

    def __post_init__(self):
        self._data = {}
        self._logged = self.__try_to_login()

    def __try_to_login(self) -> bool:
        login = self.config.get('login', '')
        password = self.config.get('password', '')
        return (login == 'admin' and password == 'admin')

    def insert(self, key: str, value: Mockument) -> None:
        if not self._logged:
            logging.warning('You need to login first')
            return
        self._data[key] = value

    def get(self, key: str) -> Mockument | None:
        if not self._logged:
            logging.warning('You need to login first')
            return None
        return self._data.get(key)


EXAMPLE_DATABASE_CONFIGS = {
    'valid': {
        'login': 'admin',
        'password': 'admin',
    },
    'invalid': {
        'login': 'admin',
        'password': '?',
    },
}
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


def run_example() -> None:
    validator = phaistos.Validator.start()

    # Check the valid database configuration and mockument
    db_config_validation_results = validator.against_schema(
        EXAMPLE_DATABASE_CONFIGS['valid'],
        'MockumentDatabaseConfig'  # Name from the YAML file
    )
    assert db_config_validation_results.valid
    logging.info(f'Database {EXAMPLE_DATABASE_CONFIGS["valid"]} configuration is valid')

    # Check the valid mockument entry data
    mockument_validation_results = validator.against_schema(
        EXAMPLE_MOCKUMENTS['valid'],
        'Mockument'  # Name from the YAML file
    )
    assert mockument_validation_results.valid
    logging.info(f'Mockument {EXAMPLE_MOCKUMENTS["valid"]} data is valid')

    # Check the invalid database configuration and mockument
    db_config_validation_results = validator.against_schema(
        EXAMPLE_DATABASE_CONFIGS['invalid'],
        'MockumentDatabaseConfig'  # Name from the YAML file
    )
    assert not db_config_validation_results.valid
    logging.error(f'Database {EXAMPLE_DATABASE_CONFIGS["invalid"]} configuration is invalid')

    # Check the invalid mockument entry data
    mockument_validation_results = validator.against_schema(
        EXAMPLE_MOCKUMENTS['invalid'],
        'Mockument'  # Name from the YAML file
    )
    assert not mockument_validation_results.valid
    logging.error(f'Mockument {EXAMPLE_MOCKUMENTS["invalid"]} data is invalid')

    # Create a database instance
    database = JustPretendItsADatabase(config=EXAMPLE_DATABASE_CONFIGS['valid'])
    logging.info('Database instance created')

    # Create a valid mockument instance
    good_mockument = Mockument(**EXAMPLE_MOCKUMENTS['valid'])

    # Insert a valid mockument
    database.insert('The Room', good_mockument)  # type: ignore
    assert database.get('The Room') is not None
    logging.info('Valid mockument inserted')

    # Insert an invalid mockument - this will raise an exception (ValueError)
    try:
        bad_mockument = Mockument(**EXAMPLE_MOCKUMENTS['invalid'])  # type: ignore
        database.insert('Troll 2', bad_mockument)
    except ValueError as insert_failed:
        logging.error(f'Invalid mockument insertion failed: {str(insert_failed)}')


if __name__ == '__main__':
    # This temporary environment variable is used to point to the example schemas,
    # so that the example can be run from the examples/directory.
    example_schemas_path = os.path.join(os.path.dirname(__file__), 'schemas')
    os.environ['PHAISTOS__SCHEMA_PATH'] = example_schemas_path
    run_example()
