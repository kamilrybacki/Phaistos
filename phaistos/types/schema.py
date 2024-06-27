from __future__ import annotations
import typing

import pydantic


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


class TranspiledSchema(pydantic.BaseModel):
    __tag__: typing.ClassVar[str]
    model_config = {
        'from_attributes': True,
        'populate_by_name': True,
    }

    @classmethod
    def compile(cls, name: str, model_data: TranspiledModelData) -> type[TranspiledSchema]:
        cls.__tag__ = name.upper()
        schema: type[TranspiledSchema] = pydantic.create_model(  # type: ignore
            name,
            __base__=TranspiledSchema,
            __validators__={
                validator['name']: validator['method']
                for validator in model_data['validators']
            },
            **model_data['properties']
        )
        return schema

    def __call__(self, data: typing.Any) -> TranspiledSchema:
        return self.model_validate(data)
