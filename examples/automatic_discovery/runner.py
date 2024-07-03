import datetime
import dataclasses
import logging
import os

import phaistos


@dataclasses.dataclass
class Mockument:
    name: str
    year: int
    rating: float


@dataclasses.dataclass
class JustPretendItsADatabase:
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
        'password': 'wrong',
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


def run_example():
    validator = phaistos.Validator.start()

    # Check the valid database configuration and mockument
    db_config_validation_results = validator.against_schema(
        EXAMPLE_DATABASE_CONFIGS['valid'],
        'MockumentDatabaseConfig'  # Name from the YAML file
    )
    assert db_config_validation_results.is_valid

    # Check the valid mockument entry data
    mockument_validation_results = validator.against_schema(
        EXAMPLE_MOCKUMENTS['valid'],
        'Mockument'  # Name from the YAML file
    )
    assert mockument_validation_results.is_valid


if __name__ == '__main__':
    example_schemas_path = os.path.join(os.path.dirname(__file__), 'schemas')
    os.environ['PHAISTOS__SCHEMA_PATH'] = example_schemas_path
    run_example()
