from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import StrEnum


class EmailCodePurpose(StrEnum):
    REGISTER = "register"
    LOGIN = "login"


class SendEmailCodeRequest(BaseModel):
    email: EmailStr
    purpose: EmailCodePurpose

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class MessageResponse(BaseModel):
    message: str


class EmailCodeLoginRequest(BaseModel):
    email: EmailStr
    email_code: str = Field(
        pattern=r"^\d{6}$",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=2,
        max_length=50,
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
    )
    confirm_password: str = Field(
        min_length=8,
        max_length=72,
    )
    email_code: str = Field(
        pattern=r"^\d{6}$",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        cleaned_value = value.strip()

        if len(cleaned_value) < 2:
            raise ValueError("用户名不能少于 2 个字符")

        return cleaned_value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr


def validate_password_confirmation(
        request: RegisterRequest,
) -> None:
    if request.password != request.confirm_password:
        raise ValueError("两次输入的密码不一致")


class LoginResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str
