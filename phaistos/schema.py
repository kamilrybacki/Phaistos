from __future__ import annotations
import typing

import pydantic
import pydantic.decorator
import pydantic.typing

from phaistos.typings import TranspiledModelData


class TranspiledSchema(pydantic.BaseModel):
    """
    A Pydantic model that represents a transpiled schema.
    """
    _context: dict[str, typing.Any] = pydantic.PrivateAttr()

    # pylint: disable=protected-access
    @classmethod
    def compile(cls, name: str, model_data: TranspiledModelData) -> type[TranspiledSchema]:
        schema: type[TranspiledSchema] = pydantic.create_model(  # type: ignore
            name,
            __base__=TranspiledSchema,
            __validators__={
                validator['name']: validator['method']
                for validator in model_data['validators']
                if validator
            },
            **model_data['properties']
        )
        schema._context = model_data.get('context', {})  # type: ignore
        return schema

