import uuid

from quart import jsonify

from core.cache import Cache
from core.cloudinary_setup import CloudinaryService
from core.hash_file import ComputeHash
from core.mapper import ORMMapper
from core.media_settings import TEMP_DIR
from core.orjson_dumps import orjson_repo
from core.paginate import PaginatePage
from core.serialize_response import SerializeResponse
from models.enums import FileType
from repos.converted_repo import ConvertedRepo
from repos.upload_repo import UploadRepo
from schemas.schema import UserFileUploadSchema


class UploadService:
    def __init__(self, db):
        self.converted_repo = ConvertedRepo(db)
        self.upload_repo = UploadRepo(db)
        self.cloudinary = CloudinaryService()
        self.file_hash = ComputeHash()
        self.cache = Cache()
        self.serialize = SerializeResponse()
        self.paginate = PaginatePage()
        self.mapper = ORMMapper()

    async def get_user_upload(self, upload_id: uuid.UUID, current_user):
        if not current_user:
            return jsonify({"error": "Not Authenticated"}), 401
        user_id = current_user.id
        cache_key = f"user_upload:{user_id}:{upload_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return orjson_repo.loads(cached)
        upload = await self.upload_repo.get_user_upload(user_id, upload_id)

        if not upload:
            return jsonify({"error": "Upload not found"}), 404
        schema_obj = self.mapper.one(upload, UserFileUploadSchema)
        result = self.serialize.get_single_json_dumps(schema_obj)
        await self.cache.set(cache_key, orjson_repo.dumps(result), 3600)
        return schema_obj

    async def get_user_uploads(self, current_user, page: int = 1, per_page: int = 20):
        if not current_user:
            return jsonify({"error": "Not Authenticated"}), 401
        user_id = current_user.id
        cache_key = f"user_uploads:{user_id}:{page}:{per_page}"
        cached = await self.cache.get(cache_key)

        if cached:

            return orjson_repo.loads(cached)
        uploads = await self.upload_repo.get_all_user_uploads(user_id, page, per_page)
        if not uploads:
            return []

        schema_obj = self.mapper.many(uploads, UserFileUploadSchema)

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

    def handle_upload(
        self,
        detected_mime: str,
        file_type: FileType,
        temp_file_id: str,
        original_filename: str,
        user_id: uuid.UUID | None = None,
    ):
        public_id = None
        try:

            # filename = f"{temp_file_id}_{Path(original_filename).name}"
            # temp_path = filename
            temp_path = TEMP_DIR / temp_file_id
            resource_type = self._get_resource_type(detected_mime)
            print(f"DEBUG resource_type resolved: {repr(resource_type)}")
            cloud_result = self.cloudinary.upload_originals(
                file_path=str(temp_path),
                resource_type=resource_type,
                folder="uploads/originals",
                original_filename=original_filename,
            )
            file_url = str(cloud_result["url"])
            public_id = str(cloud_result["public_id"])
            file_hash = self.file_hash.compute_file_hash_sync(file_url)

            upload = self.upload_repo.upload(
                original_filename=original_filename,
                cloudinary_public_id=public_id,
                cloudinary_file_url=file_url,
                cloudinary_file_hash=file_hash,
                file_type=file_type,
                cloudinary_file_resource_type=resource_type,
                detected_mime=detected_mime,
                temp_file_id=str(temp_file_id),
                user_id=user_id,
            )
            return {
                "message": "Successfully uploaded",
                "upload_id": str(upload.id),

            }
        except Exception as e:
            self.upload_repo.db_rollback()
            if public_id:
                self.cloudinary.delete_file(public_id, resource_type)
            print(f"[UPLOAD ERROR] {e}")

            return {
                "error": str(e),
                "upload_id": None
            }

    async def delete_upload(self, upload_id: uuid.UUID, current_user):

        if not current_user:
            return jsonify({"error": "Not Authenticated"}), 401
        user_id = current_user.id
        upload = await self.upload_repo.get_user_upload(user_id, upload_id)
        if not upload:
            return jsonify({"error": "Upload not found"}), 404
        try:
            await self.cloudinary.delete_async_file(
                upload.cloudinary_public_id, upload.cloudinary_file_resource_type
            )
            await self.upload_repo.delete_uploads(upload_id, user_id)
            return jsonify({"message": "Upload deleted successfully"})
        except Exception as e:
            print(f"Error deleting upload: {e}")
            return jsonify({"error": "Failed to delete upload"}), 500
