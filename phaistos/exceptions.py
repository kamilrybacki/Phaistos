
class ForbiddenModuleUseInValidator(ImportError):
    def __init__(self, *args: object, name: str | None = None, path: str | None = None) -> None:
        super().__init__(*args, name=name, path=path)


class SchemaParsingException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IncorrectFieldTypeError(ValueError):
    def __init__(self, field_type: str):
        if field_type in {'dict', 'object'}:
            message = f'Instead of using {field_type}, just declare "properties" the key'
        else:
            message = f'Invalid field type: {field_type}'
        super().__init__(message)
