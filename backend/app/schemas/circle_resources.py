"""Schemas for the circle materials and future course catalogue."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CircleResourceType = Literal["material", "course"]
CircleResourceStatus = Literal["draft", "published", "archived"]


class CircleResourceItem(BaseModel):
    id: str
    resource_type: CircleResourceType
    title: str
    summary: str = ""
    subject: str = ""
    tags: list[str] = Field(default_factory=list)
    cover_url: str = ""
    share_url: str = ""
    access_code: str = ""
    instructor_name: str = ""
    course_price: float | None = None
    sort_order: int = 0
    status: CircleResourceStatus = "draft"
    published_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CircleResourceListResponse(BaseModel):
    items: list[CircleResourceItem] = Field(default_factory=list)
    count: int = 0


class CircleResourceAdminListResponse(CircleResourceListResponse):
    limit: int = 50
    offset: int = 0


class CircleResourceUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_type: CircleResourceType
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=1000)
    subject: str = Field(default="", max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=12)
    cover_url: str = Field(default="", max_length=1000)
    share_url: str = Field(default="", max_length=1000)
    access_code: str = Field(default="", max_length=120)
    instructor_name: str = Field(default="", max_length=80)
    course_price: float | None = Field(default=None, ge=0, le=999999.99)
    sort_order: int = Field(default=0, ge=-10000, le=10000)
    status: CircleResourceStatus = "draft"

    @field_validator(
        "title",
        "summary",
        "subject",
        "cover_url",
        "share_url",
        "access_code",
        "instructor_name",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: object) -> str:
        return str(value or "").strip()

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        normalized: list[str] = []
        for item in value:
            tag = str(item or "").strip()
            if tag and tag not in normalized:
                normalized.append(tag[:30])
        return normalized

    @model_validator(mode="after")
    def validate_publish_requirements(self) -> "CircleResourceUpsertRequest":
        if not self.title:
            raise ValueError("标题不能为空")
        if self.resource_type == "material" and self.status == "published" and not self.share_url:
            raise ValueError("发布推荐资料前请填写百度网盘链接")
        if self.resource_type == "course" and self.status == "published" and self.course_price is None:
            raise ValueError("发布精选课程前请填写课程价格")
        return self


class CircleResourceDeleteResponse(BaseModel):
    id: str
