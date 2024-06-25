from __future__ import annotations
import abc
import typing

import pydantic


class ParsedProperty(typing.TypedDict):
    name: str
    data: dict[str, typing.Any]


class TranspiledPropertyValidator(typing.TypedDict):
    field: str
    name: str
    method: typing.Callable


class TranspiledProperty(typing.TypedDict):
    type: type
    default: typing.Any
    validator: TranspiledPropertyValidator


class TranspiledModelData(typing.TypedDict):
    validators: list[TranspiledPropertyValidator]
    properties: dict[str, typing.Any]


class TranspiledSchema(pydantic.BaseModel, abc.ABC):
    __tag__: typing.ClassVar[str]
    model_config = {
        'from_attributes': True,
        'populate_by_name': True,
    }

    @classmethod
    def compile(cls, name: str, model_data: TranspiledModelData) -> TranspiledSchema:
        cls.__tag__ = name.upper()
        schema: TranspiledSchema = pydantic.create_model(  # type: ignore
            name,
            __base__=TranspiledSchema,
            **model_data['properties']
        )
        for validator in model_data['validators']:
            setattr(
                schema,
                validator['name'],
                validator['method']
            )
            schema.__pydantic_decorators__.field_validators[validator['field']] = validator['method']
        schema.model_rebuild()
        return schema
