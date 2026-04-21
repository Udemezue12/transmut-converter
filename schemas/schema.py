from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Optional, TypeVar

import phonenumbers
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from core.get_db import Base
from models.enums import ConversionStatus, FileType, OutputFormat, TaskStatus
from models.enums import UserRole as Role
from utils.file_detection import ALLOWED_CONVERSIONS

ModelT = TypeVar("ModelT", bound=Base)
EventPublishHook = Callable[[ModelT, uuid.UUID], Awaitable[None]]


class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: Role

    @field_validator("username")
    @classmethod
    def validate_username_length(cls, value: str):
        if not value:
            raise ValueError("Username cannot be empty.")
        if len(value) < 5:
            raise ValueError("Username must be at least 5 characters long.")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in Role:
            raise ValueError("Invalid role choice")
        return v


class UserCreate(UserBase):
    first_name: str = Field(..., min_length=3)
    last_name: str = Field(..., min_length=3)
   
    username: str = Field(..., min_length=5, max_length=20)

    password: str = Field(
        ...,
        min_length=7,
        json_schema_extra={"type": "string", "format": "password"},
    )

    confirm_password: str = Field(
        ...,
        min_length=7,
        json_schema_extra={"type": "string", "format": "password"},
    )

    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str):
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(
                    "Invalid phone number. Use full international format.")
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            raise ValueError(
                "Invalid phone number format. Use e.g. +2348012345678")

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def capitalize_names(cls, value: str):
        return value.strip().title()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        errors = []
        if len(v) < 7:
            errors.append("≥7 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("lowercase letter")
        if not re.search(r"\d", v):
            errors.append("number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("special character")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @model_validator(mode="after")
    def finalize_fields(self):
        if not self.username:
            object.__setattr__(self, "username", self.email.split("@")[0])
        # object.__setattr__(self, "name", f"{self.firstName} {self.lastName}".strip())
        return self

    @field_validator("first_name")
    @classmethod
    def validate_firstname_length(cls, value: str):
        if not value:
            raise ValueError("First Name cannot be empty.")
        if len(value) < 5:
            raise ValueError("First Name must be at least 5 characters long.")
        return value

    @field_validator("last_name")
    @classmethod
    def validate_lastname_length(cls, value: str):
        if not value:
            raise ValueError("Last Name cannot be empty.")
        if len(value) < 5:
            raise ValueError("Last Name must be at least 5 characters long.")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=7, json_schema_extra={"type": "string", "format": "password"}
    )


class EmailInput(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: Optional[str] = None
    otp: Optional[str] = None
    new_password: str = Field(
        ...,
        min_length=7,
        json_schema_extra={"type": "string", "format": "password"},
    )
    confirm_password: str = Field(
        ...,
        min_length=7,
        json_schema_extra={"type": "string", "format": "password"},
    )

    @model_validator(mode="before")
    @classmethod
    def validate_token_or_otp(cls, values):
        token = values.get("token")
        otp = values.get("otp")
        if not token and not otp:
            raise ValueError("Either token or otp must be provided")
        return values

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str):
        errors = []
        if len(v) < 7:
            errors.append("≥7 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("lowercase letter")
        if not re.search(r"\d", v):
            errors.append("number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("special character")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class VerifyEmail(BaseModel):
    token: Optional[str] = None
    otp: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_token_or_otp(cls, values):
        token = values.get("token")
        otp = values.get("otp")
        if not token and not otp:
            raise ValueError("Either token or otp must be provided")
        return values


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class UserFileUploadSchema(BaseModel):
    id: uuid.UUID
    cloudinary_public_id: str
    cloudinary_file_hash: str
    cloudinary_file_url: str
    original_filename: str
    detected_mime: str
    file_type: FileType
    # output_formats: list[OutputFormat]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UploadDeleteRequest(BaseModel):
    public_ids: list[str]


class DetectResponse(BaseModel):

    mime:            str
    file_type:       FileType
    allowed_formats: list[OutputFormat]
    file_size:       int
    temp_file_id:    str
    filename:str


class ConvertRequest(BaseModel):
    temp_file_id:  str
    mime:          str
    file_type:     FileType
    output_format: OutputFormat
    filename:str

    @field_validator("temp_file_id")
    @classmethod
    def validate_temp_file_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("temp_file_id cannot be empty")

        if not re.fullmatch(r"[a-f0-9]{32}", v):
            raise ValueError("temp_file_id must be a valid 32-char hex string")
        return v

    @field_validator("mime")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("mime cannot be empty")

        if not re.fullmatch(r"[a-z0-9]+/[a-z0-9][a-z0-9!#$&\-^_.+]*", v):
            raise ValueError(f"Invalid mime type format: {v!r}")
        return v

    @model_validator(mode="after")
    def validate_format_matches_file_type(self):
        allowed = ALLOWED_CONVERSIONS.get(self.file_type)
        if allowed is None:
            raise ValueError(
                f"No conversions available for file_type: {self.file_type}")
        if self.output_format not in allowed:
            raise ValueError(
                f"output_format {self.output_format!r} is not valid for "
                f"file_type {self.file_type!r}. Allowed: {[f.value for f in allowed]}"
            )
        return self


class TaskAccepted(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.PENDING


class TaskResult(BaseModel):
    task_id: str
    status: str
    output_format: str | None = None
    temp_file_id: str | None = None
    error: str | None = None
    download_url: Optional[str] = None
    filename:     Optional[str] = None


class FileUpload(BaseModel):

    model_config = {
        "json_schema_extra": {
            "type": "object",
            "properties": {
                "file": {
                    "type":        "string",
                    "format":      "binary",
                    "description": "Any file — type is auto-detected from content",
                }
            },
            "required": ["file"],
        }
    }
class UploadMiniSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:uuid.UUID
    
    cloudinary_file_url: str
    original_filename: str
    detected_mime: str
    file_type: str
    created_at: datetime


class UserFileConvertedUploadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    upload: UploadMiniSchema 
    id: uuid.UUID
    upload_id: uuid.UUID
    output_format: OutputFormat
    status: ConversionStatus
    result_cloudinary_url: str
    completed_at: datetime
   
