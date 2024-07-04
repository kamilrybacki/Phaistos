from __future__ import annotations
import dataclasses
import typing

import pydantic

from phaistos.typings import TranspiledModelData, FieldValidationErrorInfo, ValidationResults


class TranspiledSchema(pydantic.BaseModel):
    """
    A Pydantic model that represents a transpiled schema.
    """
    model_config = {
        'from_attributes': True,
        'populate_by_name': True,
    }

    @classmethod
    def compile(cls, name: str, model_data: TranspiledModelData) -> type[TranspiledSchema]:
        schema: type[TranspiledSchema] = pydantic.create_model(  # type: ignore
            name,
            __base__=TranspiledSchema,
            __validators__={
                validator['name']: validator['method']
                for validator in model_data['validator']
            },
            **model_data['properties']
        )
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
        try:
            self._model(**data)
            return ValidationResults(
                valid=True,
                schema=self._model.model_json_schema(),
                errors=[],
                data=data
            )
        except pydantic.ValidationError as validation_error:
            return ValidationResults(
                valid=False,
                schema=self._model.model_json_schema(),
                errors=[
                    FieldValidationErrorInfo(
                        name=str(error['loc'][0]),
                        message=error['msg']
                    )
                    for error in validation_error.errors()
                ],
                data=data
            )

    def __call__(self, *args: typing.Any, **kwds: typing.Any) -> TranspiledSchema:
        return self._model(*args, **kwds)
