from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    nickname: str | None = Field(default=None, max_length=40)
    exam_target: str | None = Field(default=None, pattern="^(Z001|Z002)$")
    verification_code: str = Field(min_length=4, max_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SendEmailCodeRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=6)


class MessageResponse(BaseModel):
    detail: str


class AuthUser(BaseModel):
    id: str
    email: str
    nickname: str | None = None
    exam_target: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    user: AuthUser
