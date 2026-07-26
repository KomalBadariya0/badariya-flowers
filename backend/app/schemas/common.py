"""
Small shared response shapes.

Field names across every schema in this package are camelCase on purpose
— they match exactly what the existing admin JS (CategoryAPI, ProductAPI,
etc.) and the customer website already send/expect, so the frontend swap
from localStorage to fetch() needs zero shape changes.
"""
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int


class MessageResponse(BaseModel):
    success: bool = True
    message: str