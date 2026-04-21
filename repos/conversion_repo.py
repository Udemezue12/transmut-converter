import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from models.enums import ConversionStatus, OutputFormat
from models.models import Conversion, Upload


class ConvertedRepo:
    def __init__(self, db):
        self.db = db

    async def get_user_conversion(self, user_id: uuid.UUID, converted_id: uuid.UUID) -> Optional[Conversion]:
        result = await self.db.execute(
            select(Conversion)
            .join(Conversion.upload)
            .where(Upload.user_id == user_id, Conversion.id == converted_id)
            .options(selectinload(Conversion.upload))
        )
        return result.scalar_one_or_none()
    def sync_get_user_conversion(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> Optional[Conversion]:
        result = self.db.execute(
            select(Conversion)
            .join(Conversion.upload)
            .where(Upload.user_id == user_id, Conversion.upload_id == upload_id)
            .options(selectinload(Conversion.upload))
        )
        return result.scalar_one_or_none()
   

    async def get_all_user_conversions(
        self, user_id: uuid.UUID, upload_id: uuid.UUID, page: int = 1, per_page=20
    ) -> list[Conversion]:
        result = await self.db.execute(
            select(Conversion)
            .join(Conversion.upload)
            .where(Upload.user_id == user_id,Conversion.upload_id == upload_id)
            .options(selectinload(Conversion.upload))
            .order_by(Conversion.completed_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all()
    async def get_all_user_file_conversions(
        self, user_id: uuid.UUID,  page: int = 1, per_page=20
    ) -> list[Conversion]:
        result = await self.db.execute(
            select(Conversion)
            .join(Conversion.upload)
            .where(Upload.user_id == user_id)
            .options(selectinload(Conversion.upload))
            .order_by(Conversion.completed_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all()

    def upload_converted(
        self,
        upload_id: uuid.UUID,
        output_format: OutputFormat,
        status: ConversionStatus,
        celery_task_id:str, 
        error_message:str,
        result_cloudinary_public_id: str,
        result_cloudinary_file_hash: str,
        result_cloudinary_file_url: str,
        
    ):
        try:
            upload = Conversion(
                upload_id=upload_id,
                status=status,
                output_format=output_format,
                result_cloudinary_file_hash=result_cloudinary_file_hash,
                result_cloudinary_url=result_cloudinary_file_url,
                result_cloudinary_public_id=result_cloudinary_public_id,
                celery_task_id=celery_task_id,
                error_message=error_message,
                completed_at=datetime.utcnow()
            )
            self.db.add(upload)
            self.db.commit()
            
        except SQLAlchemyError:
            self.db.rollback()
            raise

    async def delete_uploads(self, converted_id: uuid.UUID):
        try:
            await self.db.execute(
                delete(Conversion).where(Conversion.id == converted_id)
            )
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise
    def db_rollback(self):
        self.db.rollback()