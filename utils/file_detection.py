import magic
from models.enums import FileType, OutputFormat

MIME_TO_FILE_TYPE = {
    "application/pdf": FileType.DOCUMENT,
    "application/msword": FileType.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCUMENT,
    "text/plain": FileType.DOCUMENT,
    "text/html": FileType.DOCUMENT,
    "application/epub+zip": FileType.DOCUMENT,
    "video/mp4": FileType.VIDEO,
    "video/x-msvideo": FileType.VIDEO,
    "video/quicktime": FileType.VIDEO,
    "video/webm": FileType.VIDEO,
    "video/x-matroska": FileType.VIDEO,
    "image/png": FileType.IMAGE,
    "image/jpeg": FileType.IMAGE,
    "image/webp": FileType.IMAGE,
    "image/gif": FileType.IMAGE,
    "image/bmp": FileType.IMAGE,
    "image/tiff": FileType.IMAGE,
    "image/x-icon": FileType.IMAGE,
    "image/vnd.microsoft.icon": FileType.IMAGE,
    "image/svg+xml": FileType.IMAGE,
    "audio/mpeg": FileType.AUDIO,
    "audio/wav": FileType.AUDIO,
    "audio/ogg": FileType.AUDIO,
}
MIME_TO_CONTENT_TYPE = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "html": "text/html",
    "epub": "application/epub+zip",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "avi": "video/x-msvideo",
    "mov": "video/quicktime",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "ico": "image/x-icon",
    "gif": "image/gif"
}
MIME_TO_OUTPUT_FORMAT = {
    "application/pdf": OutputFormat.PDF,
    "application/msword": OutputFormat.DOCX,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": OutputFormat.DOCX,
    "text/plain": OutputFormat.TXT,
    "text/html": OutputFormat.HTML,
    # "application/epub+zip": OutputFormat.EPUB,
    "video/mp4": OutputFormat.MP4,
    "video/webm": OutputFormat.WEBM,
    "video/x-msvideo": OutputFormat.AVI,
    "video/quicktime": OutputFormat.MOV,
    "image/png": OutputFormat.PNG,
    "image/jpeg": OutputFormat.JPEG,
    "image/jpg": OutputFormat.JPG,
    "image/bmp": OutputFormat.BMP,
    "image/tiff": OutputFormat.TIFF,
    "image/ico": OutputFormat.ICO,
    "image/webp": OutputFormat.WEBP,
    "audio/mpeg": OutputFormat.MP3,
    "audio/wav": OutputFormat.WAV,
    "audio/ogg": OutputFormat.OGG,
}
ALLOWED_CONVERSIONS: dict[FileType, list[OutputFormat]] = {
    FileType.DOCUMENT: [
        OutputFormat.PDF,
        OutputFormat.DOCX,
        OutputFormat.TXT,
        OutputFormat.HTML,
        # OutputFormat.EPUB
    ],
    FileType.VIDEO: [
        OutputFormat.MP4,
        OutputFormat.WEBM,
        OutputFormat.AVI,
        OutputFormat.MOV,
    ],
    FileType.IMAGE: [
        OutputFormat.PNG,
        OutputFormat.JPG,
        OutputFormat.JPEG,
        OutputFormat.WEBP,
        OutputFormat.GIF,
        OutputFormat.BMP,
        OutputFormat.TIFF,
        OutputFormat.ICO,
    ],
    FileType.AUDIO: [OutputFormat.MP3, OutputFormat.WAV, OutputFormat.OGG],
}


def detect(file_bytes: bytes) -> tuple[str, FileType, list[OutputFormat]]:
    mime = magic.from_buffer(file_bytes, mime=True)
    file_type = MIME_TO_FILE_TYPE.get(mime, FileType.DOCUMENT)
    allowed = ALLOWED_CONVERSIONS[file_type]
    return mime, file_type, allowed


def detect_v2(file_bytes: bytes) -> tuple[str, FileType, list[str]]:
    mime = magic.from_buffer(file_bytes, mime=True)
    file_type = MIME_TO_FILE_TYPE.get(mime, FileType.DOCUMENT)
    all_allowed = ALLOWED_CONVERSIONS[file_type]
    own_format = MIME_TO_OUTPUT_FORMAT.get(mime)
    allowed = [fmt.value for fmt in all_allowed if fmt != own_format]

    return mime, file_type, allowed


def detect_v3(file_bytes: bytes, filename: str) -> tuple[str, FileType, list[str]]:
    mime = magic.from_buffer(file_bytes, mime=True)
    mime = (mime or "").lower()

    ext = (filename.split(".")[-1] if "." in filename else "").lower()

    file_type = MIME_TO_FILE_TYPE.get(mime)

    if not file_type:
        if mime.startswith("image/"):
            file_type = FileType.IMAGE
        elif mime.startswith("video/"):
            file_type = FileType.VIDEO
        elif mime.startswith("audio/"):
            file_type = FileType.AUDIO

    if not file_type:
        if ext in ["png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico"]:
            file_type = FileType.IMAGE
        elif ext in ["mp4", "avi", "mov", "webm", "mkv"]:
            file_type = FileType.VIDEO
        elif ext in ["mp3", "wav", "ogg"]:
            file_type = FileType.AUDIO
        else:
            file_type = FileType.DOCUMENT

    allowed_formats = ALLOWED_CONVERSIONS.get(file_type, [])
    allowed = [f.value for f in allowed_formats]

    return mime, file_type, allowed


def get_mime_from_output_format_v1(output_format: OutputFormat) -> str:
    key = output_format.value.lower()
    mime = MIME_TO_CONTENT_TYPE.get(key)

    if not mime:
        raise ValueError(f"No MIME mapping for output format: {output_format}")

    return mime

def get_mime_from_output_format(output_format: OutputFormat) -> str:
    key = output_format.value.lower()


    if key == "jpeg":
        key = "jpg"

    mime = MIME_TO_CONTENT_TYPE.get(key)

    if not mime:
        raise ValueError(f"No MIME mapping for output format: {output_format}")

    return mime