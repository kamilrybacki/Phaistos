import dataclasses
import datetime


class ForbiddenModuleUseInValidator(ImportError):
    def __init__(self, *args: object, name: str | None = None, path: str | None = None) -> None:
        super().__init__(*args, name=name, path=path)


class SchemaLoadingException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IncorrectFieldTypeError(ValueError):
    def __init__(self, field_type: str):
        if field_type in {'dict', 'object'}:
            message = f'Instead of using {field_type}, just declare "properties" the key'
        else:
            message = f'Invalid field type: {field_type}'
        super().__init__(message)


@dataclasses.dataclass(kw_only=True)
class FieldValidationErrorInfo:
    """
    A dataclass that represents a field validation error.

    Attributes:
        name (str): The name of the field.
        message (str): The message of the field.
        timestamp (datetime.datetime): The timestamp of the error.
    """
    name: str
    message: str
    timestamp: datetime.datetime = dataclasses.field(
        default_factory=datetime.datetime.now
    )

    def __str__(self) -> str:
        formatted_timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f'{formatted_timestamp} {self.name}: {self.message}'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldValidationErrorInfo):
            return False
        return (
            self.name == other.name and self.message == other.message
        )

    def __hash__(self) -> int:
        return hash((self.name, self.message))
