from pathlib import Path

from quart import Request, jsonify, send_from_directory

from core.media_settings import MEDIA_DIR
from utils.file_detection import MIME_TO_CONTENT_TYPE


class ServeMediaService:
    

    async def serve_converted_file(self, filename: str,request: Request):
        mime_type = request.args.get("mime_type")

        if not mime_type:
            ext = Path(filename).suffix.lower().strip(".")
            mime_type = MIME_TO_CONTENT_TYPE.get(ext)

        file_path = MEDIA_DIR / filename
        if not file_path.exists():
            return jsonify({"error": "File not found", "filename": filename}), 404

        return await send_from_directory(
            MEDIA_DIR,
            filename,
            as_attachment=True,
            mimetype=mime_type,
            attachment_filename=filename
        )

   
    async def preview_file(self, request: Request, filename: str):
        mime_type = request.args.get("mime_type")

        if not mime_type:
            ext = Path(filename).suffix.lower().strip(".")
            mime_type = MIME_TO_CONTENT_TYPE.get(ext)

        file_path = MEDIA_DIR / filename
        if not file_path.exists():
            return jsonify({"error": "File not found", "filename": filename}), 404

        return await send_from_directory(
            MEDIA_DIR,
            filename,
            as_attachment=False,   
            mimetype=mime_type,
        )
