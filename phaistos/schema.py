from __future__ import annotations
import dataclasses
import logging

import pydantic

from phaistos.typings import TranspiledModelData, FieldValidationError, ValidationResults


class TranspiledSchema(pydantic.BaseModel):
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
                for validator in model_data['validators']
            },
            **model_data['properties']
        )
        return schema


@dataclasses.dataclass(kw_only=True)
class ValidationSchema:
    name: str
    _model: type[TranspiledSchema]

    def validate(self, data: dict, logger: logging.Logger) -> ValidationResults:
        try:
            self._model(**data)
            logger.info("Data is valid against schema")
            return ValidationResults(
                valid=True,
                schema=self._model.model_json_schema(),
                errors=[],
                data=data
            )
        except pydantic.ValidationError as validation_error:
            logger.error(
                f'Validation error: {validation_error}'
            )
            return ValidationResults(
                valid=False,
                schema=self._model.model_json_schema(),
                errors=[
                    FieldValidationError(
                        name=str(error['loc'][0]),
                        message=error['msg']
                    )
                    for error in validation_error.errors()
                ],
                data=data
            )
