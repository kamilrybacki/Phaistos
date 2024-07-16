import logging
from typing import ClassVar

import phaistos
import phaistos.typings


class ValidationFunctionsCompiler:
    _logger: ClassVar[logging.Logger] = ...
    @classmethod
    def compile(cls, prop: phaistos.typings.ParsedProperty) -> phaistos.typings.CompiledValidator: ...
    @classmethod
    def _compile_for_field(cls, prop: phaistos.typings.ParsedProperty) -> phaistos.typings.CompiledValidator: ...
    @classmethod
    def _compile_for_model(cls, prop: phaistos.typings.ParsedProperty) -> phaistos.typings.CompiledValidator: ...
    @staticmethod
    def _compile_validator(data: dict) -> function: ...
