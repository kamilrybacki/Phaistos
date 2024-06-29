from __future__ import annotations
import dataclasses
import typing


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
    validators: list[TranspiledPropertyValidator]
    properties: dict[str, typing.Any]


@dataclasses.dataclass(kw_only=True)
class FieldValidationError:
    name: str
    message: str


@dataclasses.dataclass(kw_only=True)
class ValidationResults:
    valid: bool
    schema: dict
    errors: list[FieldValidationError]
    data: dict = dataclasses.field(default_factory=dict)
