from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Status = Literal["active", "inactive"]


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    slug: str = Field(..., min_length=1, max_length=160)
    tagline: Optional[str] = Field(None, max_length=255)
    image: Optional[str] = None
    status: Status = "active"
    sortOrder: int = Field(1, ge=1)

    @field_validator("name", "slug")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field cannot be blank")
        return v.strip()


class CategoryUpdate(CategoryCreate):
    pass


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    tagline: Optional[str] = None
    image: Optional[str] = None
    totalProducts: int = 0
    status: Status
    sortOrder: int
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}