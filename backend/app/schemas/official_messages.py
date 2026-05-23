from pydantic import BaseModel, Field


class OfficialMessagePayload(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=2000)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    expires_at: str | None = None


class OfficialMessageItem(BaseModel):
    id: str
    title: str
    content: str
    status: str
    published_at: str | None = None
    expires_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    read: bool = False


class OfficialMessageListResponse(BaseModel):
    items: list[OfficialMessageItem]
    unread_count: int = 0


class OfficialMessageReadResponse(BaseModel):
    ok: bool = True


class OfficialMessageAdminListResponse(BaseModel):
    items: list[dict]
    count: int
