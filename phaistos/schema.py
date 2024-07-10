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
    _global_validator: typing.Optional[typing.Callable[[TranspiledSchema, typing.Any], None]] = pydantic.PrivateAttr()

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
        if model_data.get('global_validator'):
            schema._global_validator = model_data.get('global_validator')
        return schema

    # pylint: disable=not-callable
    def model_post_init(self, __context: typing.Any) -> None:
        if self._global_validator:
            self._global_validator(self, __context)

    # pylint: disable=no-self-argument, unused-variable, super-init-not-called
    def __init__(__pydantic_self__, **data: typing.Any) -> None:  # type: ignore
        """
            A modified version of the Pydantic BaseModel __init__ method that
            passed the context to the validator of __pydantic_self__.
        """
        __tracebackhide__ = True
        __pydantic_self__.__pydantic_validator__.validate_python(
            data,
            self_instance=__pydantic_self__,
            context=__pydantic_self__._context
        )
