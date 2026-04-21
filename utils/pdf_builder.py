

from __future__ import annotations

import io
import re

from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PDFBuilder:

    def __init__(self) -> None:
        base = getSampleStyleSheet()

        self.heading1 = ParagraphStyle(
            "H1", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=20, leading=26,
            textColor=colors.HexColor("#111827"),
            spaceBefore=18, spaceAfter=8,
        )
        self.heading2 = ParagraphStyle(
            "H2", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=15, leading=20,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=14, spaceAfter=6,
        )
        self.heading3 = ParagraphStyle(
            "H3", parent=base["Heading3"],
            fontName="Helvetica-BoldOblique", fontSize=12, leading=16,
            textColor=colors.HexColor("#374151"),
            spaceBefore=10, spaceAfter=4,
        )
        self.body = ParagraphStyle(
            "Body", parent=base["BodyText"],
            fontName="Helvetica", fontSize=11, leading=17,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=6,
        )
        self.bullet = ParagraphStyle(
            "Bullet", parent=self.body,
            leftIndent=18, bulletIndent=6, spaceAfter=4,
        )
        self.code = ParagraphStyle(
            "Code", parent=base["Code"],
            fontName="Courier", fontSize=9, leading=13,
            textColor=colors.HexColor("#e2e8f0"),
            backColor=colors.HexColor("#1e293b"),
            leftIndent=12, rightIndent=12,
            spaceBefore=6, spaceAfter=6,
        )

    def _table_flowable(self, rows: list[list[str]]):
        if not rows:
            return None
        t = Table(rows, hAlign="LEFT", repeatRows=1)
        header_bg = colors.HexColor("#1e40af")
        grid = colors.HexColor("#d1d5db")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("GRID",       (0, 0), (-1, -1), 0.5, grid),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.HexColor("#ffffff"),
                colors.HexColor("#f3f4f6"),
            ]),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))
        return t

    def build(self, story_items: list) -> bytes:
        buffer = io.BytesIO()
        try:
            doc = SimpleDocTemplate(
                buffer, pagesize=A4,
                leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                topMargin=2.5 * cm, bottomMargin=2.5 * cm,
            )
            doc.build(story_items)
            buffer.seek(0)
            result = buffer.read()
        finally:
            buffer.close()
        return result

    def html_to_story(self, html: str) -> list:
        """Convert an HTML string into a ReportLab story list."""
        soup = BeautifulSoup(html, "html.parser")
        story = []

        def _escape(s: str) -> str:
            return (s.replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;"))

        def walk(tag):
            for el in tag.children:
                name = getattr(el, "name", None)
                text = _escape(el.get_text(" ", strip=True)
                               ) if hasattr(el, "get_text") else ""

                if name == "h1":
                    story.append(Paragraph(text, self.heading1))
                elif name == "h2":
                    story.append(Paragraph(text, self.heading2))
                elif name in ("h3", "h4", "h5", "h6"):
                    story.append(Paragraph(text, self.heading3))
                elif name == "p":
                    if text:
                        story.append(Paragraph(text, self.body))
                elif name in ("ul", "ol"):
                    for li in el.find_all("li", recursive=False):
                        li_text = _escape(li.get_text(" ", strip=True))
                        story.append(
                            Paragraph(li_text, self.bullet, bulletText="•"))
                elif name == "table":
                    rows = []
                    for tr in el.find_all("tr"):
                        row = [_escape(td.get_text(" ", strip=True))
                               for td in tr.find_all(["th", "td"])]
                        if row:
                            rows.append(row)
                    if rows:
                        t = self._table_flowable(rows)
                        if t:
                            story.append(t)
                            story.append(Spacer(1, 0.15 * cm))
                elif name in ("pre", "code"):
                    story.append(Paragraph(_escape(el.get_text()), self.code))
                elif name == "blockquote":
                    story.append(Paragraph(text, self.body))
                elif name in ("div", "section", "article", "main", "body", "html"):
                    walk(el)
                elif name in ("br",):
                    story.append(Spacer(1, 0.2 * cm))
                elif name == "hr":
                    story.append(Spacer(1, 0.4 * cm))
                # skip head, style, script, etc.

        walk(soup)
        if not story:
            story.append(Paragraph("(empty document)", self.body))
        return story

    def txt_to_story(self, text: str) -> list:

        story = []
        table_rows: list[list[str]] = []
        in_table = False

        def flush_table():
            nonlocal in_table, table_rows
            if table_rows:
                t = self._table_flowable(table_rows)
                if t:
                    story.append(t)
                    story.append(Spacer(1, 0.2 * cm))
            table_rows = []
            in_table = False

        for line in text.splitlines():
            stripped = line.strip()

            if not stripped:
                if in_table:
                    flush_table()
                story.append(Spacer(1, 0.15 * cm))
                continue

            if stripped.startswith("# "):
                if in_table:
                    flush_table()
                story.append(Paragraph(stripped[2:], self.heading1))
                continue
            if stripped.startswith("## "):
                if in_table:
                    flush_table()
                story.append(Paragraph(stripped[3:], self.heading2))
                continue
            if stripped.startswith("### "):
                if in_table:
                    flush_table()
                story.append(Paragraph(stripped[4:], self.heading3))
                continue

            if stripped.startswith(("- ", "* ", "+ ")):
                if in_table:
                    flush_table()
                story.append(
                    Paragraph(stripped[2:], self.bullet, bulletText="•"))
                continue

            if re.match(r"^\d+\.\s", stripped):
                if in_table:
                    flush_table()
                story.append(Paragraph(stripped, self.bullet))
                continue

            if "|" in stripped and not stripped.startswith("|-"):
                row = [c.strip() for c in stripped.split("|") if c.strip()]
                if row:
                    table_rows.append(row)
                    in_table = True
                continue
            elif in_table and re.match(r"^[\-\| :]+$", stripped):
                continue  # markdown table separator row
            else:
                if in_table:
                    flush_table()

            # inline bold
            formatted = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
            formatted = re.sub(r"\*(.*?)\*", r"<i>\1</i>", formatted)
            story.append(Paragraph(formatted, self.body))

        if in_table:
            flush_table()
        return story or [Paragraph("(empty document)", self.body)]
