from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: str
    full_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UserUpdateEmail(BaseModel):
    new_email: EmailStr


class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = None
