"""Pydantic compatibility layer providing graceful fallback if running pre-install.
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field, EmailStr
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    class BaseModel:
        model_config = {}

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self, *args, **kwargs):
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "model_dump"):
                    res[k] = v.model_dump()
                elif isinstance(v, list):
                    res[k] = [item.model_dump() if hasattr(item, "model_dump") else item for item in v]
                else:
                    res[k] = v
            return res

        @classmethod
        def model_validate(cls, obj, *args, **kwargs):
            if isinstance(obj, dict):
                return cls(**obj)
            attrs = {}
            for k in dir(obj):
                if not k.startswith("_"):
                    try:
                        val = getattr(obj, k)
                        if not callable(val):
                            attrs[k] = val
                    except Exception:
                        pass
            return cls(**attrs)

    def Field(default=None, **kwargs):
        default_factory = kwargs.get("default_factory")
        if default_factory:
            try:
                return default_factory()
            except Exception:
                return []
        return default

    EmailStr = str
