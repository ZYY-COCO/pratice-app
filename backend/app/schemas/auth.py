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


class SendPhoneCodeRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    purpose: str = Field(pattern="^(login|register)$")


class PhoneRegisterRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    verification_code: str = Field(min_length=4, max_length=8)
    nickname: str | None = Field(default=None, max_length=40)
    exam_target: str | None = Field(default=None, pattern="^(Z001|Z002)$")


class PhoneLoginRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    verification_code: str = Field(min_length=4, max_length=8)


class PhoneCodeResponse(BaseModel):
    detail: str
    debug_code: str | None = None


class WechatAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class WechatLoginRequest(BaseModel):
    code: str | None = None
    state: str | None = None
    redirect_uri: str | None = None


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=6)


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=40)
    avatar_url: str | None = Field(default=None, max_length=120)
    gender: str | None = Field(default=None, pattern="^(male|female)$")
    exam_target: str | None = Field(default=None, pattern="^(Z001|Z002)$")


class ChangeEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=4, max_length=8)


class MessageResponse(BaseModel):
    detail: str


class AuthUser(BaseModel):
    id: str
    email: str
    phone: str | None = None
    auth_provider: str | None = None
    wechat_openid: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    gender: str | None = None
    exam_target: str | None = None
    membership_status: str | None = "inactive"
    membership_plan: str | None = None
    membership_started_at: str | None = None
    membership_expires_at: str | None = None
    membership_updated_at: str | None = None
    role: str | None = "user"
    disabled_at: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    user: AuthUser
