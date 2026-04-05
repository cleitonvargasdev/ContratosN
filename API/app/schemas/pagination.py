from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10


ItemType = TypeVar("ItemType")


class PaginatedResponse(BaseModel, Generic[ItemType]):
    items: list[ItemType]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
            }
        }
    )
