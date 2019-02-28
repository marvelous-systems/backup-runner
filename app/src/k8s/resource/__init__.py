from enum import IntEnum, auto
from typing import Dict, Union, List

import logger

__author__ = "Noah Hummel"
log = logger.get(__name__)


def strip_null(resource: Union[Dict, List]) -> Union[Dict, List]:
    if type(resource) is dict:
        retval = dict()
        for k, v in resource.items():
            if type(v) is dict:
                retval[k] = strip_null(v)
            elif v is not None:
                retval[k] = v
        return retval
    elif type(resource) is list:
        return [strip_null(x) for x in resource]
    else:
        return resource


def snake_case(identifier: str) -> str:
    class State(IntEnum):
        Init = auto()
        Upper = auto()
        Lower = auto()

    retval = ""
    state = State.Init
    next_state = State.Init
    for char in identifier:
        # state transition
        if not char.isalpha():
            next_state = State.Lower
        elif char.isupper():
            next_state = State.Upper
        else:
            next_state = State.Lower

        # output
        if state == State.Lower and next_state == State.Upper:
            retval += f"_{char.lower()}"
        else:
            retval += char.lower()

        state = next_state

    return retval


def camel_case(identifier: str) -> str:
    retval = ""

    class State(IntEnum):
        Init = auto()
        Word = auto()
        Separator = auto()

    state = State.Init
    next_state = State.Init
    for char in identifier:
        if char == "_":
            next_state = State.Separator
        else:
            next_state = State.Word

        # output
        if state == State.Separator and next_state == State.Word:
            retval += char.upper() if char.isalpha() else char
        elif next_state != State.Separator:
            retval += char

        state = next_state

    return retval


def to_snake_case(resource: Union[Dict, List]) -> Union[Dict, List]:
    if type(resource) is dict:
        retval = dict()
        for k, v in resource.items():
            new_k = snake_case(k)
            new_v = to_snake_case(v)
            retval[new_k] = new_v
        return retval
    elif type(resource) is list:
        return [to_snake_case(x) for x in resource]
    else:
        return resource


def to_camel_case(resource: Union[Dict, List]) -> Union[Dict, List]:
    if type(resource) is dict:
        retval = dict()
        for k, v in resource.items():
            new_k = camel_case(k)
            new_v = to_camel_case(v)
            retval[new_k] = new_v
        return retval
    elif type(resource) is list:
        return [to_camel_case(x) for x in resource]
    else:
        return resource