import asyncio
import logging
import httpx
import hashlib
import time
import cloudinary
import cloudinary.api
import cloudinary.uploader
from quart import Request, abort
from werkzeug.exceptions import HTTPException
from pathlib import Path

from core.settings import settings
from security.user_generate import user_generate

logger = logging.getLogger(__name__)


class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_SECRET_KEY,
            secure=True,
        )

    def upload_converted(
        self,
        file_path,
        resource_type: str,
        original_filename: str,
        folder: str = "uploads",

    ) -> dict:
        if not file_path:
            abort(500, "Generated file not found")
        base_name = Path(original_filename).stem  # alembic
        random_id = user_generate.generate_secure_cloudinary_public_id()
        result = cloudinary.uploader.upload(
            file_path,
            public_id=f"{random_id}_{base_name}",
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            folder=folder,
        )
        return {
            "public_id": result["public_id"],
            "url": result["secure_url"],
            "format": result.get("format"),
            "bytes": result.get("bytes"),
        }

    def upload_originals(
        self,
        file_path,
        resource_type: str,
        original_filename: str,
        folder: str = "uploads",
    ) -> dict:
        if not file_path:
            abort(500, "Generated file not found")

        base_name = Path(original_filename).stem  # alembic
        random_id = user_generate.generate_secure_cloudinary_public_id()



        try:

            result = cloudinary.uploader.upload(
                str(file_path),
                resource_type=resource_type,
                folder=folder,
                public_id=f"{random_id}_{base_name}",
                use_filename=True,
                filename_override=original_filename,
            )
            print("FINAL resource_type BEFORE UPLOAD:",
                  repr(result["resource_type"]))
            print("FILE PATH:", file_path)
            return {
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "format": result.get("format"),
                "bytes": result.get("bytes"),
            }

        except Exception as e:
            abort(500, f"Signed PDF upload failed: {e}")

    def delete_file(self, public_id: str, resource_type) -> dict:
        return cloudinary.uploader.destroy(
            public_id, resource_type=resource_type, invalidate=True
        )

    async def delete_async_file(self, public_id: str, resource_type) -> dict:
        return cloudinary.uploader.destroy(
            public_id, resource_type=resource_type, invalidate=True
        )

    async def delete_file_async(self, public_id: str, resource_type: str) -> dict:
        timestamp = int(time.time())

        params = f"invalidate=true&public_id={public_id}&resource_type={resource_type}&timestamp={timestamp}"
        signature = hashlib.sha256(
            f"{params}{cloudinary.config().api_secret}".encode()
        ).hexdigest()

        cloud_name = cloudinary.config().cloud_name
        api_key = cloudinary.config().api_key

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/destroy",
                data={
                    "public_id": public_id,
                    "signature": signature,
                    "api_key": api_key,
                    "timestamp": timestamp,
                    "invalidate": True,
                }
            )
            response.raise_for_status()
            return response.json()

    async def delete_resources(self, public_ids: list[str]) -> dict:
        if not public_ids:
            abort(code=400, description="No public_ids provided")

        try:
            loop = asyncio.get_running_loop()

            def delete_all():
                results = {}

                for resource_type in ["image", "raw", "video"]:
                    res = cloudinary.api.delete_resources(
                        public_ids,
                        resource_type=resource_type,
                        invalidate=True,
                    )
                    results[resource_type] = res

                return results

            result = await loop.run_in_executor(None, delete_all)

            return {
                "message": "Deletion attempted across all resource types",
                "results": result,
            }

        except Exception as e:
            abort(code=500, description=f"Failed to delete resources: {e}")

    async def list_resources(
        self,
        *,
        request: Request,
        folder: str | None = None,
        max_results: int = 50,
        next_cursor: str | None = None,
    ) -> dict:
        VALID_RESOURCE_TYPES = frozenset({"image", "video", "raw"})
        try:
            resource_type = request.args.get("resource_type")

            if resource_type and resource_type not in VALID_RESOURCE_TYPES:
                abort(
                    400,
                    description=f"Invalid resource_type '{resource_type}'. Must be one of: {', '.join(sorted(VALID_RESOURCE_TYPES))}.",
                )

            base_params = {
                "type": "upload",
                "max_results": max_results,
                **({"prefix": folder} if folder else {}),
                **({"next_cursor": next_cursor} if next_cursor else {}),
            }

            types_to_fetch = (
                [resource_type] if resource_type else list(
                    VALID_RESOURCE_TYPES)
            )

            results: dict[str, list] = {}
            errors: dict[str, str] = {}

            for rtype in types_to_fetch:
                try:
                    response = cloudinary.api.resources(
                        **base_params, resource_type=rtype
                    )
                    results[rtype] = response.get("resources", [])
                except Exception as e:
                    errors[rtype] = str(e)
                    logger.warning(
                        "Failed to fetch Cloudinary resources for type '%s': %s",
                        rtype,
                        e,
                    )

            payload: dict = {"resources": results}

            if errors:
                payload["errors"] = errors

            return payload

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error in list_resources: %s",
                         e, exc_info=True)
            abort(500, description=f"Failed to list Cloudinary resources: {e}")


cloudinary_service = CloudinaryService()
