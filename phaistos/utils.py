import copy
import logging
import re

import pydantic.fields
import pydantic_core

import phaistos.exceptions
import phaistos.consts
from phaistos.typings import (
    TranspiledProperty,
    ParsedProperty,
    RawValidator
)
from phaistos.sources import COLLECTION_VALIDATOR_TEMPLATE


def setup_logger(logger_name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO)
    new_logger = logging.getLogger(logger_name)
    new_logger.propagate = False
    new_logger.handlers.clear()
    log_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    new_logger.addHandler(log_handler)
    new_logger.setLevel(logging.DEBUG)
    return new_logger


def block(*args, **kwargs):
    raise phaistos.exceptions.ForbiddenModuleUseInValidator()


def check_if_collection_is_allowed(collection_type: str) -> None:
    if collection_type not in phaistos.consts.ALLOWED_COLLECTION_TYPES:
        raise phaistos.exceptions.IncorrectFieldTypeError(collection_type)


def construct_field_annotation(property_data: TranspiledProperty) -> tuple[type, pydantic.fields.FieldInfo]:
    return (
        property_data['type'],
        pydantic.fields.FieldInfo(
            default=property_data.get(
                'default',
                pydantic_core.PydanticUndefined
            ),
            **property_data['constraints']
        )
    )


def adjust_collection_type_property_entry(prop: ParsedProperty) -> ParsedProperty:
    adjusted = copy.deepcopy(prop)
    validator_data = adjusted['data'].get('validator', RawValidator({
        'source': '',
        'mode': 'after'
    }))
    if match := re.match(
        phaistos.consts.COLLECTION_TYPE_REGEX,
        adjusted['data']['type']
    ):
        check_if_collection_is_allowed(match['collection'])
        adjusted['data']['validator'] = RawValidator(
            source=validator_data['source'] + COLLECTION_VALIDATOR_TEMPLATE % (
                match['item'],
                adjusted['name'],
                match['item']
            ),
            mode=validator_data['mode']
        )
        adjusted['data']['type'] = match['collection']
    else:
        adjusted['data']['validator'] = validator_data
    return adjusted


def check_for_forbidden_imports(source: str) -> None:
    if any(
        any(
            pattern in source
            for pattern in [f'import {module}', f'{module}.']
        )
        for module in phaistos.consts.BLOCKED_MODULES
    ):
        raise phaistos.exceptions.ForbiddenModuleUseInValidator()
