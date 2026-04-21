

from __future__ import annotations

import io
import os
import re
import subprocess
import tempfile
import unicodedata
import uuid
from pathlib import Path
from typing import Callable

import html2text
import mammoth
import pdfplumber
from bs4 import BeautifulSoup
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from ebooklib import epub
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .acessories import run


def html_template(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 16px;
      line-height: 1.8;
      color: #1a1a1a;
      background: #fff;
      max-width: 860px;
      margin: 0 auto;
      padding: 48px 32px;
    }}
    h1, h2, h3, h4 {{
      font-family: 'Helvetica Neue', Arial, sans-serif;
      color: #111;
      margin-top: 1.8em;
      margin-bottom: 0.4em;
    }}
    h1 {{ font-size: 2em; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.3em; }}
    h2 {{ font-size: 1.5em; }}
    h3 {{ font-size: 1.2em; }}
    p  {{ margin: 0.75em 0; }}
    ul, ol {{ margin: 0.75em 0; padding-left: 1.6em; }}
    li {{ margin: 0.3em 0; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 1.2em 0;
      font-size: 0.95em;
    }}
    th, td {{
      border: 1px solid #d1d5db;
      padding: 10px 14px;
      text-align: left;
    }}
    th {{
      background: #1e40af;
      color: #fff;
      font-family: Arial, sans-serif;
      font-size: 0.9em;
      font-weight: 600;
    }}
    tr:nth-child(even) {{ background: #f3f4f6; }}
    code  {{ background: #f1f5f9; padding: 2px 5px; border-radius: 3px; font-size: 0.88em; }}
    pre   {{ background: #1e293b; color: #e2e8f0; padding: 1em; border-radius: 6px; overflow-x: auto; }}
    pre code {{ background: none; padding: 0; }}
    blockquote {{
      border-left: 4px solid #6366f1;
      margin: 1em 0;
      padding: 0.5em 1em;
      color: #4b5563;
      background: #f8f9ff;
    }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""


def clean_text(text: str) -> str:

    text = unicodedata.normalize("NFC", text)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def make_epub(html_body: str) -> bytes:
    book = epub.EpubBook()

    
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(" ")     
    book.set_language(" ")
    book.add_author(" ")   

    
    css_content = """
    body { font-family: Georgia, serif; font-size: 1em; line-height: 1.7; margin: 1em; }
    h1, h2, h3 { font-family: Arial, sans-serif; }
    h1 { font-size: 1.8em; }
    h2 { font-size: 1.4em; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; }
    th { background: #1e40af; color: white; }
    code { background: #f1f5f9; padding: 2px 4px; }
    """

    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=css_content,
    )
    book.add_item(nav_css)

    # Chapter
    chapter = epub.EpubHtml(file_name="content.xhtml", lang="en")

    chapter.content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <link rel="stylesheet" href="style/nav.css" type="text/css"/>
</head>
<body>
{html_body}
</body>
</html>
"""

    chapter.add_item(nav_css)
    book.add_item(chapter)

    # ✅ FIXED TOC (this was your crash point)
    book.toc = (
        epub.Link("content.xhtml", "Content", "content"),
    )

    # Required navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Spine
    book.spine = ["nav", chapter]

    # Write EPUB safely
    buf = io.BytesIO()

    try:
        epub.write_epub(buf, book)
        buf.seek(0)
        data = buf.read()
    except Exception as e:
        raise RuntimeError(f"EPUB generation failed: {e}")
    finally:
        buf.close()

    return data


def epub_to_html_body(content: bytes) -> tuple[str, str]:

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "input.epub"
        src.write_bytes(content)
        out = Path(tmp) / "output.html"
        run(["pandoc", str(src), "-t", "html", "-o", str(out)])
        html = out.read_text("utf-8")

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Document"
    body = soup.find("body")
    body_html = body.decode_contents() if body else html
    return title, body_html


def html_to_docx_bytes(html: str) -> bytes:

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "input.html"
        src.write_text(html, encoding="utf-8")
        out = Path(tmp) / "output.docx"
        run(["pandoc", str(src), "-o", str(out)])
        return out.read_bytes()


def docx_to_html(content: bytes) -> str:

    result = mammoth.convert_to_html(io.BytesIO(content))
    return result.value
