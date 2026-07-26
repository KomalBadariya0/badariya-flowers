from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

CatalogueType = Literal["master", "category"]


class CatalogueRead(BaseModel):
    id: int
    type: CatalogueType
    categoryId: Optional[int] = None
    subCategoryId: Optional[int] = None
    title: str
    fileUrl: str
    fileSize: Optional[int] = None
    uploadedAt: datetime

    model_config = {"from_attributes": True}