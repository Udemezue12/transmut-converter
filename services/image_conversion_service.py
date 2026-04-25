import io

from PIL import Image as PILImage, UnidentifiedImageError

from models.enums import OutputFormat


class ImageConverter:
    @classmethod
    def convert(cls, content: bytes, output_format: OutputFormat) -> bytes:
       
        

        try:
            img: PILImage.Image = PILImage.open(io.BytesIO(content))
            img.load()
        except UnidentifiedImageError:
            raise ValueError("Invalid image file")

        fmt_map = {
            OutputFormat.PNG: "PNG",
            OutputFormat.JPG: "JPEG",
            OutputFormat.JPEG: "JPEG",
            OutputFormat.WEBP: "WEBP",
            OutputFormat.GIF: "GIF",
            OutputFormat.BMP: "BMP",
            OutputFormat.TIFF: "TIFF",
            OutputFormat.ICO: "ICO",
            
        }

        pil_fmt = fmt_map.get(output_format)
        if not pil_fmt:
            raise ValueError(f"Unsupported image format: {output_format}")

        if pil_fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffer = io.BytesIO()

        try:
            save_kwargs = {}

            if pil_fmt == "JPEG":
                save_kwargs.update({"quality": 85, "optimize": True})
            elif pil_fmt == "WEBP":
                save_kwargs.update({"quality": 80})
            elif pil_fmt == "PNG":
                save_kwargs.update({"optimize": True})

            img.save(buffer, format=pil_fmt, **save_kwargs)
            buffer.seek(0)
            return buffer.read()
        finally:
            buffer.close()