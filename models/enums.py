from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class ENVSettings(str, Enum):
    Production = "Production"


class ConversionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"


class OutputFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    EPUB = "epub"

    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    WEBM = "webm"
    MKV = "mkv"

    PNG  = "png"
    JPG  = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF  = "gif"
    BMP  = "bmp"
    TIFF = "tiff"
    ICO  = "ico"

    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    PROCESSING = "PROCESSING"
    STARTED= "STARTED"
    FAILURE = "FAILURE"
    SUCCESS="SUCCESS"
