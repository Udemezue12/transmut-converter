def build_preview_page(filename: str, download_url: str, output_format: str) -> str:
    
    image_formats   = {"png", "jpg", "jpeg", "webp", "gif", "svg"}
    video_formats   = {"mp4", "webm", "ogg"}
    audio_formats   = {"mp3", "wav", "ogg", "m4a"}
    document_formats = {"pdf"}

    if output_format in image_formats:
        preview_block = f'<img src="{download_url}" alt="{filename}" class="preview-media" />'

    elif output_format in video_formats:
        preview_block = f"""
        <video controls class="preview-media">
            <source src="{download_url}" type="video/{output_format}">
            Your browser does not support the video tag.
        </video>"""

    elif output_format in audio_formats:
        preview_block = f"""
        <audio controls class="preview-audio">
            <source src="{download_url}" type="audio/{output_format}">
            Your browser does not support the audio tag.
        </audio>"""

    elif output_format in document_formats:
        preview_block = f'<iframe src="{download_url}" class="preview-iframe" title="{filename}"></iframe>'

    else:
        
        preview_block = """
        <div class="no-preview">
            <p>Preview not available for this file type.</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview — {filename}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: system-ui, sans-serif;
            background: #0f0f0f;
            color: #f0f0f0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
        }}
        .container {{
            width: 100%;
            max-width: 900px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .filename {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #e0e0e0;
            word-break: break-all;
        }}
        .download-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #2563eb;
            color: white;
            padding: 0.6rem 1.4rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95rem;
            transition: background 0.2s;
            white-space: nowrap;
        }}
        .download-btn:hover {{ background: #1d4ed8; }}
        .preview-wrapper {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 300px;
            padding: 1rem;
        }}
        .preview-media {{
            max-width: 100%;
            max-height: 70vh;
            border-radius: 8px;
        }}
        .preview-audio {{
            width: 100%;
        }}
        .preview-iframe {{
            width: 100%;
            height: 70vh;
            border: none;
            border-radius: 8px;
        }}
        .no-preview {{
            text-align: center;
            padding: 3rem;
            color: #888;
            font-size: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="filename">📄 {filename}</span>
            <a href="{download_url}" download="{filename}" class="download-btn">
                ⬇ Download
            </a>
        </div>
        <div class="preview-wrapper">
            {preview_block}
        </div>
    </div>
</body>
</html>"""