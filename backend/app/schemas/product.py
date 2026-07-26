from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SpecificationItem(BaseModel):
    label: str
    value: str


class SeoInfo(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    slug: Optional[str] = None


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    categoryId: Optional[int] = None
    subCategoryId: int
    sku: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    priceNote: Optional[str] = None
    moq: int = Field(1, ge=1)

    shortDesc: Optional[str] = None
    fullDesc: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None

    tags: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)  # pre-uploaded URLs, from /api/products/{id}/images

    featured: bool = False
    active: bool = True

    specifications: List[SpecificationItem] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    usage: Optional[str] = None
    careInstructions: Optional[str] = None

    seo: Optional[SeoInfo] = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field cannot be blank")
        return v.strip()


class ProductUpdate(ProductCreate):
    pass


class ProductRead(BaseModel):
    id: int
    no: int
    name: str
    categoryId: Optional[int] = None
    subCategoryId: int
    sku: Optional[str] = None
    price: Optional[float] = None
    priceNote: Optional[str] = None
    priceLabel: str
    moq: int

    shortDesc: Optional[str] = None
    fullDesc: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None

    tags: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)

    featured: bool
    active: bool

    specifications: List[SpecificationItem] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    usage: Optional[str] = None
    careInstructions: Optional[str] = None

    seo: SeoInfo

    createdAt: datetime