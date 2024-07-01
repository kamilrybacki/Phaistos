from __future__ import annotations
import dataclasses
import typing

from phaistos.consts import DEFAULT_INDENTATION


class RawSchemaProperty(typing.TypedDict):
    description: str
    type: typing.NotRequired[str]
    default: typing.NotRequired[typing.Any]
    validator: typing.NotRequired[str]
    properties: typing.NotRequired[dict[str, RawSchemaProperty]]


class SchemaInputFile(typing.TypedDict):
    version: str
    name: str
    properties: dict[str, RawSchemaProperty]


class ParsedProperty(typing.TypedDict):
    name: str
    data: dict[str, typing.Any]


class TranspiledPropertyValidator(typing.TypedDict):
    field: str
    name: str
    method: typing.Any


class TranspiledProperty(typing.TypedDict):
    type: type
    default: typing.Any
    validator: TranspiledPropertyValidator


class TranspiledModelData(typing.TypedDict):
    validator: list[TranspiledPropertyValidator]
    properties: dict[str, typing.Any]


@dataclasses.dataclass(kw_only=True)
class FieldValidationErrorInfo:
    name: str
    message: str

    def __str__(self) -> str:
        return f'{self.name}: {self.message}'


@dataclasses.dataclass(kw_only=True)
class ValidationResults:
    valid: bool
    schema: dict
    errors: list[FieldValidationErrorInfo]
    data: dict = dataclasses.field(default_factory=dict)

    def __str__(self) -> str:
        is_data_valid = 'Yes' if self.valid else 'No'
        errors_printout = '\nReasons:\n' + '\n'.join(
            f'{DEFAULT_INDENTATION}{error}'
            for error in self.errors
        ) if self.errors else ""
        return f'Is data valid?: {is_data_valid}{errors_printout}'
