# pylint: disable=wrong-import-position
import copy
import os
import textwrap
import types

import pytest

os.environ['PHAISTOS__DISABLE_SCHEMA_DISCOVERY'] = 'True'

import consts  # noqa: E402  # type: ignore

import phaistos.validator  # noqa: E402
import phaistos.consts  # noqa: E402


@pytest.mark.parametrize(
    'hot_patch, exception',
    consts.SCHEMA_DISCOVERY_FAIL_CASES,
    ids=[
        exception.__name__
        for _, exception in consts.SCHEMA_DISCOVERY_FAIL_CASES
    ]
)
def test_schema_discovery_exceptions(
    hot_patch: str,
    exception: type[Exception],
    logger,
    monkeypatch
):
    logger.info(f'Testing schema discovery exception: {exception.__name__}')

    original_get_available_schemas = copy.deepcopy(
        phaistos.Validator.get_available_schemas  # pylint: disable=protected-access
    )

    original_schema_path = copy.deepcopy(
        os.environ.get('PHAISTOS__SCHEMA_PATH', '')
    )

    def patched_get_available_schemas():
        patch_function = types.FunctionType(
            compile(
                textwrap.dedent(hot_patch),
                '',
                'exec'
            ),
            globals=globals()
        )
        patch_function()  # pylint: disable=not-callable
        return original_get_available_schemas()

    monkeypatch.setattr(
        phaistos.Validator,
        'get_available_schemas',
        patched_get_available_schemas
    )

    with pytest.raises(exception):
        phaistos.Validator.get_available_schemas()  # pylint: disable=protected-access
    logger.info(f'Successfully tested schema discovery exception: {exception.__name__}')
    os.environ['PHAISTOS__SCHEMA_PATH'] = original_schema_path
