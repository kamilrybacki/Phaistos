from __future__ import annotations
import copy
import dataclasses
import typing

import pydantic
import pydantic.decorator
import pydantic.typing

from phaistos.typings import TranspiledModelData, ValidationResults
from phaistos.exceptions import FieldValidationErrorInfo


# pylint: disable=unused-private-member
class TranspiledSchema(pydantic.BaseModel):
    """
    A Pydantic model that represents a transpiled schema.
    """
    transpilation_name: typing.ClassVar[str] = ''
    global_validator: typing.ClassVar[
        typing.Callable[[TranspiledSchema, typing.Any], None] | None
    ] = None
    context: typing.ClassVar[
        dict[str, typing.Any]
    ] = {}
    _validation_errors: typing.ClassVar[
        list[FieldValidationErrorInfo]
    ] = []
    parent: typing.ClassVar[type[TranspiledSchema]]

    # pylint: disable=protected-access
    @property
    def validation_errors(self) -> list[FieldValidationErrorInfo]:
        return self.parent._validation_errors

    # pylint: disable=protected-access
    @classmethod
    def compile(cls, model_data: TranspiledModelData) -> type[TranspiledSchema]:
        if not model_data.get('parent'):
            cls._validation_errors = []
        schema: type[TranspiledSchema] = pydantic.create_model(  # type: ignore
            model_data['name'],
            __base__=TranspiledSchema,
            __validators__={
                validator['name']: validator['method']
                for validator in model_data['validators']
                if validator
            },
            **model_data['properties']
        )
        schema.parent = model_data.get('parent') or copy.deepcopy(cls)
        cls._rename_schema(schema, model_data['name'])

        schema.context = model_data.get('context', {})  # type: ignore
        schema.global_validator = model_data.get('global_validator')
        return schema

    @classmethod
    def _rename_schema(cls, schema: type[TranspiledSchema], name: str) -> None:
        for field in ['__name__', '__qualname__', 'transpilation_name']:
            if hasattr(schema, field):
                setattr(schema, field, name)

    # pylint: disable=no-self-argument, unused-variable, super-init-not-called, not-callable
    def __init__(self, **data: typing.Any) -> None:  # type: ignore
        """
            A modified version of the Pydantic BaseModel __init__ method that
            passed the context to the validator.
        """
        __tracebackhide__ = True
        collected_errors: list[FieldValidationErrorInfo] = []
        try:
            if self.global_validator:
                self.global_validator(data)  # type: ignore
        except Exception as validator_exception:  # pylint: disable=broad-except
            collected_errors.append(
                FieldValidationErrorInfo(
                    name=self.__class__.__name__,
                    message=str(validator_exception)
                )
            )
        try:
            self.__pydantic_validator__.validate_python(
                data,
                self_instance=self,
                context=self.context
            )
        except pydantic.ValidationError as validation_error:
            collected_errors.extend([
                FieldValidationErrorInfo(
                    name=str(error['loc'][0]) if error['loc'] else validation_error.title,
                    message=error['msg']
                )
                for error in validation_error.errors()
            ])
        self.parent._validation_errors += self._validation_errors + collected_errors


@dataclasses.dataclass(kw_only=True)
class SchemaInstancesFactory:
    """
    A dataclass that represents a validation schema.

    Attributes:
        name (str): The name of the schema.
        _model (type[TranspiledSchema]): The model of the schema, used for validation.
    """
    name: str
    _model: type[TranspiledSchema]
    errors: list[FieldValidationErrorInfo] = dataclasses.field(default_factory=list)

    def validate(self, data: dict) -> ValidationResults:
        """
        Validate the given data against the schema. Do not return
        the validated data, only the validation results.

        Args:
            data (dict): The data to validate.

        Returns:
            ValidationResults: The validation results, including the schema, errors, and data.
        """
        self._model(**data)
        collected_errors = [
            *set(self._model.parent._validation_errors)  # pylint: disable=protected-access
        ]
        self.errors = collected_errors
        return ValidationResults(
            schema=self._model.model_json_schema(),
            errors=collected_errors,
            data=data
        )

    def build(self, data: dict[str, typing.Any]) -> TranspiledSchema | None:
        self.errors = []
        validation = self.validate(data)
        return self._model(**data) if validation.valid else None
