from __future__ import annotations
import typing

import pydantic
import pydantic.decorator
import pydantic.typing

from phaistos.typings import TranspiledModelData
from phaistos.exceptions import FieldValidationErrorInfo


# pylint: disable=unused-private-member
class TranspiledSchema(pydantic.BaseModel):
    """
    A Pydantic model that represents a transpiled schema.
    """
    _context: dict[str, typing.Any] = pydantic.PrivateAttr({})
    global_validator: typing.ClassVar[
        typing.Callable[[TranspiledSchema, typing.Any], None] | None
    ]
    global_validation_error: typing.ClassVar[FieldValidationErrorInfo | None] = None

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
        schema.global_validator = model_data.get('global_validator')
        return schema

    # pylint: disable=no-self-argument, unused-variable, super-init-not-called, not-callable
    def __init__(self, **data: typing.Any) -> None:  # type: ignore
        """
            A modified version of the Pydantic BaseModel __init__ method that
            passed the context to the validator.
        """
        __tracebackhide__ = True
        try:
            if self.__class__.global_validator:
                self.__class__.global_validator(data)  # type: ignore
        except Exception as validator_exception:  # pylint: disable=broad-except
            self.__class__.global_validation_error = FieldValidationErrorInfo(
                name=self.__class__.__name__,
                message=str(validator_exception)
            )
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context=self._context
        )
