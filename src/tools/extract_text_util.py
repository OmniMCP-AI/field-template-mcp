import re
from typing import TypeVar

import structlog
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger()


def extract_json_str(s: str) -> str:
    if match := re.search(r"```(?:json)?(.+)```", s, re.DOTALL):
        return match[1]

    if match := re.search(r"`(.+)`", s):
        return match[1]

    return s.strip("`")


_T_MODEL = TypeVar("_T_MODEL", bound="BaseModel")


def extract_json(s: str, model: type[_T_MODEL]) -> _T_MODEL | None:
    if json_str := extract_json_str(s):
        try:
            return model.model_validate_json(json_str)
        except ValidationError as e:
            logger.exception(
                "Failed to validate JSON", json_str=json_str, model=model, exc_info=e
            )
            return None

    return None
