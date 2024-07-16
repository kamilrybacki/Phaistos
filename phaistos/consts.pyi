from typing import ClassVar
from types import ModuleType

class NullModule(ModuleType):
    LOCK: ClassVar[bool]
    def __getattr__(self, *args, **kwargs): ...

ALLOWED_COLLECTION_TYPES: set
COLLECTION_TYPE_REGEX: str
BLOCKED_MODULES: list
ISOLATION_FROM_UNWANTED_LIBRARIES: dict
DISCOVERY_EXCEPTIONS: dict
