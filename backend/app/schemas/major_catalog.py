from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


MajorCatalogFavoriteTargetType = Literal["school", "program"]


class MajorCatalogFavoriteRef(BaseModel):
    catalog_year: str = Field(pattern=r"^20\d{2}$")
    target_type: MajorCatalogFavoriteTargetType
    target_id: str = Field(min_length=1, max_length=128)


class MajorCatalogFavoriteStatusRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[MajorCatalogFavoriteRef] = Field(
        min_length=1,
        max_length=200,
        alias="refs",
        serialization_alias="refs",
    )


class MajorCatalogFavoriteStatusItem(MajorCatalogFavoriteRef):
    is_favorited: bool
    available: bool


class MajorCatalogFavoriteStatusResponse(BaseModel):
    items: list[MajorCatalogFavoriteStatusItem] = Field(default_factory=list)


class MajorCatalogFavoriteItem(MajorCatalogFavoriteRef):
    id: str
    school_id: str
    snapshot: dict[str, Any] = Field(default_factory=dict)
    available: bool
    created_at: str
    updated_at: str


class MajorCatalogFavoriteListResponse(BaseModel):
    items: list[MajorCatalogFavoriteItem] = Field(default_factory=list)
    count: int = 0
    next_cursor: str | None = None
    has_more: bool = False


class MajorCatalogFavoriteMutationResponse(MajorCatalogFavoriteRef):
    is_favorited: bool
    available: bool | None = None
    snapshot: dict[str, Any] | None = None
