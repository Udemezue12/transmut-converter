import os
import subprocess
import tempfile


from models.enums import OutputFormat


class AudioVideoConverter:
    
    

    @classmethod
    def convert(cls, content: bytes, input_ext: str, output_format: OutputFormat) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, f"input.{input_ext}")
            dst = os.path.join(tmp, f"output.{output_format.value}")
            with open(src, "wb") as f:
                f.write(content)
            subprocess.run(
                ["ffmpeg", "-y", "-i", src, dst],
                check=True, capture_output=True,
            )
            with open(dst, "rb") as f:
                return f.read()