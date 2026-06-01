from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    last_name: str
    first_name: str
    patronymic: str | None = None
    phone: str | None = None
    role: str
    role_label: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ProfileUpdateRequest(BaseModel):
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    phone: str | None = None
