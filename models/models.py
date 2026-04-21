import uuid
from datetime import datetime
from typing import Optional

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.get_db import Base
from encryption_file.encypted_string import EncryptedString

from .enums import ConversionStatus, FileType, OutputFormat, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(EncryptedString, nullable=False)

    last_name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(EncryptedString, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), nullable=False, default=None
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow()
    )
    uploads: Mapped[list["Upload"]] = relationship(
        "Upload",
        back_populates="user_uploads",
        cascade="all, delete-orphan",
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True)

    def set_password(self, raw_password: str):
        salt = gensalt()
        self.hashed_password = hashpw(raw_password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, raw_password: str) -> bool:
        return checkpw(
            raw_password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )

    @hybrid_property
    def full_name(self) -> str:
        parts = [
            self.first_name,
            self.last_name,
        ]
        return " ".join(p for p in parts if p)


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    __table_args__ = (Index("idx_blacklisted_token", "token"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False)
    blacklisted_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Upload(Base):
    __tablename__ = "uploads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    original_filename: Mapped[str] = mapped_column(
        EncryptedString(255), nullable=False)
    temp_file_id: Mapped[str] = mapped_column(String(512), nullable=False)
    cloudinary_public_id: Mapped[str] = mapped_column(
        EncryptedString(255), nullable=False)
    cloudinary_file_hash: Mapped[str] = mapped_column(
        EncryptedString(512), nullable=False)
    cloudinary_file_url: Mapped[str] = mapped_column(
        EncryptedString(512), nullable=False
    )
    cloudinary_file_resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    file_type: Mapped[Enum] = mapped_column(Enum(FileType), nullable=False)
    detected_mime: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    user_uploads: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="uploads",
    )
    conversions: Mapped[list["Conversion"]] = relationship(
        "Conversion", back_populates="upload", cascade="all, delete-orphan"
    )


class Conversion(Base):
    __tablename__ = "conversions"
    __table_args__ = (
        UniqueConstraint("upload_id", "output_format", name="uq_upload_output"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False
    )
    output_format: Mapped[Enum] = mapped_column(
        Enum(OutputFormat), nullable=False)
    status: Mapped[Enum] = mapped_column(
        Enum(ConversionStatus), default=ConversionStatus.PENDING
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    result_cloudinary_public_id: Mapped[str] = mapped_column(
        EncryptedString(255), nullable=True)
    result_cloudinary_file_hash: Mapped[str] = mapped_column(
        String(255), nullable=True)
    result_cloudinary_url: Mapped[str] = mapped_column(
        EncryptedString(512), nullable=True
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, index=True)

    upload: Mapped["Upload"] = relationship(
        "Upload", back_populates="conversions")
