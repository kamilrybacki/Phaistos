from __future__ import annotations
import dataclasses
import typing

import pydantic
import pydantic.decorator
import pydantic.typing

from phaistos.typings import TranspiledModelData, FieldValidationErrorInfo, ValidationResults


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


@dataclasses.dataclass(kw_only=True)
class ValidationSchema:
    """
    A dataclass that represents a validation schema.

    Attributes:
        name (str): The name of the schema.
        _model (type[TranspiledSchema]): The model of the schema, used for validation.
    """
    name: str
    _model: type[TranspiledSchema]

    def validate(self, data: dict) -> ValidationResults:
        """
        Validate the given data against the schema. Do not return
        the validated data, only the validation results.

        Args:
            data (dict): The data to validate.

        Returns:
            ValidationResults: The validation results, including the schema, errors, and data.
        """
        collected_errors: list[FieldValidationErrorInfo] = []
        self._run_validators(data, collected_errors)
        return ValidationResults(
            valid=not collected_errors,
            schema=self._model.model_json_schema(),
            errors=collected_errors,
            data=data
        )

    def _run_validators(self, data: dict, collected_errors: list[FieldValidationErrorInfo]) -> None:
        try:
            self._model.model_validate(
                data,
                context=self._model._context  # pylint: disable=protected-access
            )
        except pydantic.ValidationError as validation_error:
            collected_errors.extend([
                FieldValidationErrorInfo(
                    name=str(error['loc'][0]) if error['loc'] else '__root__',
                    message=error['msg']
                )
                for error in validation_error.errors()
            ])

    def __call__(self, *args: typing.Any, **kwds: typing.Any) -> TranspiledSchema:
        return self._model(*args, **kwds)
