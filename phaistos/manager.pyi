import logging
from phaistos.schema import SchemaInstancesFactory, TranspiledSchema
from phaistos.typings import SchemaInputFile, ValidationResults
from typing import ClassVar

DISCOVERY_EXCEPTIONS: dict


class Manager:
    logger: ClassVar[logging.Logger]
    _current_schemas_path: ClassVar[str]
    _schemas: ClassVar[dict]
    _started: ClassVar[bool]
    __instance: ClassVar[None]

    def validate(self, data: dict, schema: str) -> ValidationResults: ...
    @classmethod
    def start(cls, discover: bool = ..., schemas_path: str | None = ...) -> Manager: ...
    @classmethod
    def _purge(cls) -> None: ...
    def __init__(self, discover: bool) -> None: ...
    def get_factory(self, name: str) -> SchemaInstancesFactory:
        """
        Get a schema factory by name

        Args:
            name (str): The name of the schema

        Returns:
            SchemaInstancesFactory: The schema factory, that can be used to validate data and create instances of the model
        """
    def get_available_schemas(self) -> dict[str, SchemaInstancesFactory]: ...
    def __discover_schemas(self, target_path: str) -> list[type[TranspiledSchema]]: ...
    def load_schema(self, schema: SchemaInputFile) -> str: ...
