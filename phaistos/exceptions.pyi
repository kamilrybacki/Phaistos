import datetime

class ForbiddenModuleUseInValidator(ImportError): ...

class SchemaLoadingException(Exception): ...

class IncorrectFieldTypeError(ValueError): ...

class FieldValidationErrorInfo:
    name: str
    message: str
    timestamp: datetime.datetime
