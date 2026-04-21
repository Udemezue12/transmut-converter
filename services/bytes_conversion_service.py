from models.enums import FileType, OutputFormat

from .audio_conversion_service import AudioVideoConverter
from .document_conversion import DocumentConverter
from .image_conversion_service import ImageConverter


def convert_bytes(
    content: bytes,
    mime: str,
    file_type: FileType,
    output_format: OutputFormat,
) -> bytes:
    if file_type == FileType.DOCUMENT:
        return DocumentConverter.convert(content, mime, output_format)

    if file_type == FileType.IMAGE:
        return ImageConverter.convert(content, output_format)

    if file_type in (FileType.VIDEO, FileType.AUDIO):
        input_ext = mime.split("/")[-1].replace("x-", "").replace("mpeg", "mp3")
        return AudioVideoConverter.convert(content, input_ext, output_format)

    raise ValueError(f"No converter for file type: {file_type}")
