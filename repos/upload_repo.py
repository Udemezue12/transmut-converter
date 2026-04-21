import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from models.enums import FileType
from models.models import Upload


class UploadRepo:
    def __init__(self, db):
        self.db = db

    async def get_user_upload(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> Optional[Upload]:
        result = await self.db.execute(
            select(Upload)
            .where(Upload.user_id == user_id, Upload.id == upload_id)
            .options(
                selectinload(Upload.user_uploads), selectinload(
                    Upload.conversions)
            )
        )
        return result.scalar_one_or_none()

    def sync_get_upload_id(self, upload_id: uuid.UUID | None) -> Optional[Upload]:
        result = self.db.execute(
            select(Upload)
            .where(Upload.id == upload_id)
            .options(
                selectinload(Upload.user_uploads), selectinload(
                    Upload.conversions)
            )
        )
        return result.scalar_one_or_none()

    async def get_all_user_uploads(
        self, user_id: uuid.UUID, page: int = 1, per_page=20
    ) -> list[Upload]:
        result = await self.db.execute(
            select(Upload)
            .where(Upload.user_id == user_id)
            .options(
                selectinload(Upload.user_uploads), selectinload(
                    Upload.conversions)
            )
            .order_by(Upload.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all()

    def upload(
        self,
        user_id: uuid.UUID,
        original_filename: str,
        cloudinary_public_id: str,
        cloudinary_file_hash: str,
        cloudinary_file_url: str,
        file_type: FileType,
        detected_mime: str,
        cloudinary_file_resource_type: str,
        temp_file_id: str
    ) -> Upload:
        try:
            upload = Upload(
                user_id=user_id,
                original_filename=original_filename,
                cloudinary_file_hash=cloudinary_file_hash,
                cloudinary_file_url=cloudinary_file_url,
                cloudinary_public_id=cloudinary_public_id,
                file_type=file_type,
                detected_mime=detected_mime,
                cloudinary_file_resource_type=cloudinary_file_resource_type,

                temp_file_id=temp_file_id
            )
            self.db.add(upload)
            self.db.commit()
            self.db.refresh(upload)
            return upload
        except SQLAlchemyError:
            self.db.rollback()
            raise

    async def delete_uploads(self, upload_id: uuid.UUID, user_id: uuid.UUID):
        try:
            await self.db.execute(
                delete(Upload).where(Upload.user_id ==
                                     user_id, Upload.id == upload_id)
            )
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    def db_rollback(self):
        self.db.rollback()
