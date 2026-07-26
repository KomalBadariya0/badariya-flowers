from pydantic import BaseModel


class ProductImageRead(BaseModel):
    id: int
    productId: int
    url: str
    sortOrder: int
    isPrimary: bool

    model_config = {"from_attributes": True}