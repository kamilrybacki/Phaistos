import logging
import phaistos.typings

COLLECTION_VALIDATOR_TEMPLATE: str

def setup_logger(logger_name: str) -> logging.Logger: ...
def block(*args, **kwargs): ...
def check_if_collection_is_allowed(collection_type: str) -> None: ...
def construct_field_annotation(property_data: phaistos.typings.TranspiledProperty) -> tuple: ...
def adjust_collection_type_property_entry(prop: phaistos.typings.ParsedProperty) -> phaistos.typings.ParsedProperty: ...
def check_for_forbidden_imports(source: str) -> None: ...
