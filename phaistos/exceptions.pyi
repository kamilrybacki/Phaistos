import datetime
import dataclasses

class ForbiddenModuleUseInValidator(ImportError): ...

class SchemaLoadingException(Exception): ...

class IncorrectFieldTypeError(ValueError): ...

@dataclasses.dataclass(kw_only=True)
class FieldValidationErrorInfo:
    name: str
    message: str
    timestamp: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)
