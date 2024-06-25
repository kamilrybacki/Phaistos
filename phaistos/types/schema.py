import abc
import typing

import pydantic


# pylint: disable=too-few-public-methods
class BaseSchemaModel(pydantic.BaseModel, abc.ABC):
    __tag__: typing.ClassVar[str]

    @property  # type: ignore
    @abc.abstractmethod
    def __tag__(self) -> str:
        pass

    model_config = {
        'from_attributes': True,
        'populate_by_name': True,
    }


class ParsedProperty(typing.TypedDict):
    name: str
    data: dict[str, typing.Any]


class TranspiledProperty(typing.TypedDict):
    type: type
    default: typing.Any
    validator: typing.Callable


class _TranspiledModelDataBase(typing.TypedDict):
    __validators__: dict[str, typing.Callable]


TranspiledModelData = typing.Union[_TranspiledModelDataBase, typing.Dict]
