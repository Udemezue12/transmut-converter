import uuid
from pathlib import Path

from celery import chord
from celery.result import AsyncResult
from quart import Request, jsonify, redirect
from core.urrlib import sanitize_filename
from celery_worker.celery_app import app as task_app
from core.media_settings import TEMP_DIR
from models.enums import TaskStatus
from schemas.schema import DetectResponse, TaskResult
from utils.file_detection import ALLOWED_CONVERSIONS, MIME_TO_OUTPUT_FORMAT, detect_v3


class ConversionService:
    async def detect_file(self, request: Request, current_user=None):
        user_id = current_user.id if current_user else None
        print(f"User ID: {user_id}")
        files = await request.files
        print("Received files keys:", list(files.keys()))

        if "file" not in files:
            return jsonify(
                {
                    "error": "No file provided",
                    "received_keys": list(files.keys()),
                    "hint": "Make sure the form field name is exactly 'file'",
                }
            ), 400
        file = files["file"]
        file_bytes = file.read()
        filename = file.filename
        if not file_bytes:
            return jsonify({"error": "File is empty"}), 400

        print(
            f"Received file: {file.filename!r}, size: {len(file_bytes)} bytes")
        mime, file_type, allowed = detect_v3(file_bytes[:2048], filename)
        temp_id = uuid.uuid4().hex
        temp_path = TEMP_DIR / f"{temp_id}"
        temp_path.write_bytes(file_bytes)

        print(
            f"Saved temp file: {temp_path} | {len(file_bytes)} bytes | {mime}")

        return jsonify(
            DetectResponse(
                mime=mime,
                file_type=file_type,
                allowed_formats=allowed,
                temp_file_id=temp_id,
                file_size=len(file_bytes),
                filename=filename
            ).model_dump()
        )

    async def detect_files(self, request: Request, current_user):
        user_id = current_user.id if current_user else None
        print(f"User ID: {user_id}")
        files = await request.files

        if "file" not in files:
            return jsonify({"error": "No file provided"}), 400

        file_list = files.getlist("file")

        responses = []

        for file in file_list:
            file_bytes = file.read()
            filename = file.filename

            if not file_bytes:
                continue

            mime, file_type, allowed = detect_v3(file_bytes[:2048], filename)
            temp_id = uuid.uuid4().hex
            temp_path = TEMP_DIR / f"{temp_id}"
            temp_path.write_bytes(file_bytes)

            responses.append(
                DetectResponse(
                    mime=mime,
                    file_type=file_type,
                    allowed_formats=allowed,
                    file_size=len(file_bytes),
                    temp_file_id=temp_id,
                    filename=filename
                ).model_dump()
            )

        return jsonify({"files": responses})

    async def start_conversion(self, current_user, data):
        user_id = current_user.id if current_user else None
        header_tasks = []

        temp_path = TEMP_DIR / f"{data.temp_file_id}"
        source_format = MIME_TO_OUTPUT_FORMAT.get(data.mime)
        if source_format and source_format == data.output_format:
            return jsonify(
                {
                    "error": f"File is already in {data.output_format.value.upper()} format",
                    "source_format": source_format.value,
                    "hint": f"Choose a different output format",
                }
            ), 400

        allowed = ALLOWED_CONVERSIONS.get(data.file_type, [])
        if data.output_format not in allowed:
            return jsonify(
                {
                    "error": f"Cannot convert {data.file_type.value} to {data.output_format.value}",
                    "allowed_formats": [f.value for f in allowed],
                }
            ), 400

        if not temp_path.exists():
            return jsonify(
                {
                    "error": "Temp file not found — please re-upload",
                }
            ), 400
        filename_stem = sanitize_filename(Path(data.filename).stem)
        converted_filename = f"{filename_stem}.{data.output_format.value}"

        if user_id:
            upload_sig = task_app.signature(
                "tasks_media_upload",
                args=[
                    str(data.mime),
                    data.file_type.value,
                    str(data.temp_file_id),
                    str(user_id),
                    data.filename,
                ],
            )
            header_tasks.append(upload_sig)

        convert_sig = task_app.signature(
            "convert_media",
            kwargs={
                "temp_file_path": str(temp_path),
                "mime": str(data.mime),
                "file_type": str(data.file_type.value),
                "output_format": str(data.output_format.value),
                "filename": str(data.filename),
                "temp_file_id": str(data.temp_file_id),
            },

        )
        if header_tasks:
            job = chord(header_tasks)(convert_sig)
        else:
            job = convert_sig.apply_async()

        return jsonify({
            "task_id": job.id,
            "filename": converted_filename,
            "status": "accepted"
        }), 202

    async def get_result(self, task_id: str):
        result = AsyncResult(task_id, app=task_app)
        if not result:
            return jsonify({"error": "Task not found"}), 404

        if result.state == TaskStatus.PENDING:
            return jsonify(
                TaskResult(task_id=task_id,
                           status=TaskStatus.PENDING).model_dump()
            )

        if result.state in (TaskStatus.STARTED, TaskStatus.PROCESSING):
            return jsonify(
                TaskResult(task_id=task_id,
                           status=TaskStatus.PROCESSING).model_dump()
            )

        if result.state == TaskStatus.FAILURE:
            return jsonify(
                TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=str(result.result),
                ).model_dump()
            ), 500

        if result.state == TaskStatus.SUCCESS:
            data = result.result
            return jsonify(
                TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    output_format=data["output_format"],
                    download_url=data["download_url"],
                    filename=data["filename"],
                ).model_dump()
            )

        return jsonify({"task_id": task_id, "status": result.state.lower()})

    async def download(self, task_id: str):
        result = AsyncResult(task_id, app=task_app)

        if result.state != TaskStatus.SUCCESS:
            return jsonify(
                {
                    "error": "Conversion not ready",
                    "status": result.state.lower(),
                }
            ), 202

        data = result.result

        mime = data["mime"]
        print("Mime:", mime)

        file_url = data["download_url"]

        return redirect(file_url)
