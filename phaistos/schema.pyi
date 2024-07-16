from typing import Any, ClassVar

import pydantic._internal._decorators
import pydantic.main

from phaistos.exceptions import FieldValidationErrorInfo
from phaistos.typings import TranspiledModelData, ValidationResults


class TranspiledSchema(pydantic.main.BaseModel):
    transpilation_name: ClassVar[str]
    global_validator: ClassVar[None]
    context: ClassVar[dict]
    model_config: ClassVar[dict]
    model_computed_fields: ClassVar[dict]

    @classmethod
    def compile(cls, model_data: TranspiledModelData) -> type[TranspiledSchema]: ...
    @classmethod
    def _rename_schema(cls, schema: type[TranspiledSchema], name: str) -> None: ...
    def __init__(self, **data) -> None:
        """
            A modified version of the Pydantic BaseModel __init__ method that
            passed the context to the validator.
        """
    def model_post_init(self: pydantic.main.BaseModel, __context) -> None:
        """This function is meant to behave like a BaseModel method to initialise private attributes.

            It takes context as an argument since that's what pydantic-core passes when calling it.

            Args:
                self: The BaseModel instance.
                __context: The context.
    """
    @property
    def validation_errors(self) -> list[FieldValidationErrorInfo]: ...


class SchemaInstancesFactory:
    name: str
    _model: type[TranspiledSchema]
    errors: list[FieldValidationErrorInfo]

    def validate(self, data: dict) -> ValidationResults:
        """
        Validate the given data against the schema. Do not return
        the validated data, only the validation results.

        Args:
            data (dict): The data to validate.

        Returns:
            ValidationResults: The validation results, including the schema, errors, and data.
        """
    def build(self, data: dict[str, Any]) -> TranspiledSchema | None: ...
