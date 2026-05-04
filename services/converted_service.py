import uuid

from quart import jsonify

from core.cache import Cache
from core.cloudinary_setup import CloudinaryService
from core.hash_file import ComputeFileHash
from core.mapper import ORMMapper
from core.orjson_dumps import orjson_repo
from core.paginate import PaginatePage
from core.serialize_response import SerializeResponse
from models.enums import ConversionStatus, OutputFormat
from repos.conversion_repo import ConvertedRepo
from repos.upload_repo import UploadRepo
from schemas.schema import UserFileConvertedUploadSchema

from .tasks_queue import TaskQueue


class ConvertedFileService:
    def __init__(self, db):
        self.db = db
        self.tasks_queue = TaskQueue()
        self.converted_repo = ConvertedRepo(db)
        self.upload_repo = UploadRepo(db)
        self.cloudinary = CloudinaryService()
        self.file_hash = ComputeFileHash()
        self.cache = Cache()
        self.serialize = SerializeResponse()
        self.paginate = PaginatePage()
        self.mapper = ORMMapper()

    async def get_user_conversion(self, converted_id: uuid.UUID, current_user):
        if not current_user:
            return jsonify({"error": "Not Authenticated"}), 401
        user_id = current_user.id
        cache_key = f"user_conversion:{user_id}:{converted_id}"
        cached = await self.cache.get(cache_key)

        if cached:
            return orjson_repo.loads(cached)
        upload = await self.converted_repo.get_user_conversion(user_id, converted_id)

        if not upload:
            return jsonify({"error": "Upload not found"}), 404
        schema_obj = self.mapper.one(upload, UserFileConvertedUploadSchema)
        result = self.serialize.get_single_json_dumps(schema_obj)
        await self.cache.set(cache_key, orjson_repo.dumps(result), 3600)
        return schema_obj

    async def get_user_file_conversions(self, current_user, page: int = 1, per_page: int = 20):
        if not current_user:
            return jsonify({"error": "Not Authenticated"}), 401
        user_id = current_user.id
        cache_key = f"user_conversions:{user_id}:{page}:{per_page}"
        cached = await self.cache.get(cache_key)
        if cached:
            print(f"Cached::{cached}")
            return orjson_repo.loads(cached)
        uploads = await self.converted_repo.get_all_user_file_conversions(user_id, page, per_page)

        schema_obj = self.mapper.many(uploads, UserFileConvertedUploadSchema)

        result = self.serialize.get_list_json_dumps(schema_obj)
        paginated_result = self.paginate.paginate(result, page, per_page)
        await self.cache.set(cache_key,  orjson_repo.dumps(paginated_result), 3600)
        return paginated_result

    def _get_resource_type(self, detected_mime: str) -> str:
        if detected_mime.startswith("image/"):
            return "image"
        elif detected_mime.startswith("video/") or detected_mime.startswith("audio/"):
            return "video"
        else:
            return "raw"

    def handle_converted_upload(
        self,
        output_format: OutputFormat,
        file_path,
        resource_type: str,
        upload_id: uuid.UUID,
        status: ConversionStatus,
        celery_task_id: str,
        error_message: str,
        original_filename: str,


    ):
        public_id = None
        try:

            cloud_result = self.cloudinary.upload_converted(
                file_path=str(file_path),
                resource_type=resource_type,
                folder="uploads/converted",
                original_filename=original_filename


            )
            file_url = str(cloud_result["url"])
            public_id = str(cloud_result["public_id"])
            file_hash = self.file_hash.compute_file_hash_sync(file_url)

            self.converted_repo.upload_converted(
                upload_id=upload_id,
                status=status,
                output_format=output_format,
                result_cloudinary_file_hash=file_hash,
                result_cloudinary_file_url=file_url,
                result_cloudinary_public_id=public_id,
                error_message=error_message,
                celery_task_id=celery_task_id,




            )
            return {
                "message": "Successfully uploaded",
            }
        except Exception as e:
            self.converted_repo.db_rollback()
            if public_id:
                self.cloudinary.delete_file(public_id, resource_type)
            print(f"Error: {e}")

    async def delete_converted(
        self,
        converted_id: uuid.UUID,
        current_user,
    ):
        if not current_user:
            return {"error": "Not authenticated"}, 401

        user_id = current_user.id

        async with self.db.begin():

            converted = await self.converted_repo.get_user_conversion(
                user_id, converted_id
            )

            if not converted:
                return {"error": "Not found"}, 404

            if converted.status in [ConversionStatus.PENDING, ConversionStatus.PROCESSING]:
                return {
                    "error": "Cannot delete conversion in progress"
                }, 400

            if converted.deleted_at:
                return {"message": "Already deleted"}, 200

            await self.converted_repo.soft_delete(converted.id)

        if converted.result_cloudinary_public_id:
            self.tasks_queue.enqueue_cloudinary_delete(
                str(converted.result_cloudinary_public_id), str(
                    converted.result_cloudinary_resource_type)
            )

        return {"message": "Deleted successfully"}
