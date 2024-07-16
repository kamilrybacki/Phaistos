import logging
from typing import ClassVar

from phaistos.schema import TranspiledSchema
from phaistos.typings import CompiledValidator, ParsedProperty, SchemaInputFile, TranspiledModelData, TranspiledProperty

class Transpiler:
    _logger: ClassVar[logging.Logger]

    def __post_init__(self) -> None: ...
    @classmethod
    def make_validator(cls, prop: ParsedProperty) -> CompiledValidator | None:
        """
        Method to transpile a property's validator into a Pydantic model field validator.

        Args:
            prop (ParsedProperty): A property with its respective data, from which the validator will be extracted.

        Returns:
            TranspiledPropertyValidator: A Pydantic model field validator.
        """
    @classmethod
    def make_property(cls, prop: ParsedProperty, owner: type[TranspiledSchema] | None = ...) -> TranspiledProperty:
        """
        Method to transpile a property into a Pydantic model field.

        Args:
            prop (ParsedProperty): A property with its respective data.

        Returns:
            TranspiledProperty: A Pydantic model field.
        """
    @classmethod
    def make_properties(cls, properties: list[ParsedProperty], properties_parent: type[TranspiledSchema]) -> TranspiledModelData:
        """
        Method to read a list of properties and transpile them into a Pydantic model fields.

        Args:
            properties (list[ParsedProperty]): A list of properties with their respective data.

        Returns:
            TranspiledModelData: A dictionary with the transpiled properties.
        """
    @classmethod
    def make_schema(cls, schema: SchemaInputFile, parent: type[TranspiledSchema] | None = ...) -> type[TranspiledSchema]:
        """
        Transpile a schema into a Pydantic model.

        Args:
            schema (SchemaInputFile): A parsed schema, stored as a dictionary with typed fields.

        Returns:
            type[TranspiledSchema]: A Pydantic model class with the schema's properties.
        """
    @classmethod
    def supress_logging(cls) -> None: ...
    @classmethod
    def enable_logging(cls) -> None: ...
    def __init__(self) -> None: ...
    def __eq__(self, other) -> bool: ...
