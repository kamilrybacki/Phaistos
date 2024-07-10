from __future__ import annotations
import dataclasses
import typing


class RawSchemaProperty(typing.TypedDict):
    """
    A dictionary that represents a property in a schema.

    Attributes:
        description (str): A description of the property.
        type (str): The type of the property.
        default (typing.Any): The default value of the property.
        validator (str): The validator of the property.
        properties (dict[str, RawSchemaProperty]): The properties of the property. Can include recursive properties of RawSchemaProperty type.
    """
    description: str
    type: typing.NotRequired[str]
    default: typing.NotRequired[typing.Any]
    validator: typing.NotRequired[RawValidator]
    properties: typing.NotRequired[dict[str, RawSchemaProperty]]
    constraints: typing.NotRequired[dict[str, typing.Any]]


class RawValidator(typing.TypedDict):
    mode: typing.Literal['before', 'after', 'wrap']
    source: str


class SchemaInputFile(typing.TypedDict):
    """
    A dictionary that represents a schema input file.

    Attributes:
        version (str): The version of the schema.
        name (str): The name of the schema.
        description (str): The description of the schema.
        properties (dict[str, RawSchemaProperty]): The properties of the schema.
        context (dict[str, typing.Any]): The context of the schema, used during validation. (See: https://docs.pydantic.dev/2.0/usage/validators/#validation-context)
    """
    version: str
    name: str
    description: str
    properties: dict[str, RawSchemaProperty]
    context: typing.NotRequired[dict[str, typing.Any]]
    validator: typing.NotRequired[RawValidator]


class ParsedProperty(typing.TypedDict):
    """
    A dictionary that represents a parsed property.

    Attributes:
        name (str): The name of the property.
        data (RawSchemaProperty): The data of the property.
    """
    name: str
    data: RawSchemaProperty


class CompiledValidator(typing.TypedDict):
    """
    A dictionary that represents a transpiled property validator.

    Attributes:
        field (str): The field of the property.
        name (str): The name of the property.
        method (typing.Any): The method of the property.
    """
    field: str
    name: str
    method: typing.Any


class TranspiledProperty(typing.TypedDict):
    """
    A dictionary that represents a transpiled property.

    Attributes:
        type (typing.Any): The type of the property.
        default (typing.Any): The default value of the property.
        validator (TranspiledPropertyValidator): The validator of the property.
    """
    type: type
    default: typing.Any
    validator: CompiledValidator | None
    constraints: dict[str, typing.Any]


class TranspiledModelData(typing.TypedDict):
    """
    A dictionary that represents transpiled model data.

    Attributes:
        validator (list[TranspiledPropertyValidator]): A list of transpiled property validators.
        properties (dict[str, typing.Any]): A dictionary of transpiled properties.
        context (dict[str, typing.Any]): A dictionary of the context of the model, used during validation.
    """
    validators: list[CompiledValidator]
    properties: dict[str, typing.Any]
    context: typing.NotRequired[dict[str, typing.Any]]
    global_validator: typing.NotRequired[typing.Any]


@dataclasses.dataclass(kw_only=True)
class FieldValidationErrorInfo:
    """
    A dataclass that represents a field validation error.

    Attributes:
        name (str): The name of the field.
        message (str): The message of the field.
    """
    name: str
    message: str

    def __str__(self) -> str:
        return f'{self.name}: {self.message}'


@dataclasses.dataclass(kw_only=True)
class ValidationResults:
    """
    A dataclass that represents the results of a validation.

    Attributes:
        valid (bool): A boolean that represents if the data is valid.
        schema (dict): The schema of the data.
        errors (list[FieldValidationErrorInfo]): A list of field validation errors.
        data (dict): The data that was validated.
    """
    valid: bool
    schema: dict
    errors: list[FieldValidationErrorInfo]
    data: dict = dataclasses.field(default_factory=dict)

    def __str__(self) -> str:
        is_data_valid = 'Yes' if self.valid else 'No'
        errors_printout = '\nReasons:\n' + '\n'.join(
            f'  {error}'
            for error in self.errors
        ) if self.errors else ""
        return f'Is data valid?: {is_data_valid}{errors_printout}'
