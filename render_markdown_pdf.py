#!/usr/bin/env python3
"""Render simple markdown notes into readable PDFs."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


CODE_PLACEHOLDER = re.compile(r"`([^`]+)`")


def build_styles() -> StyleSheet1:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyTight",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletTight",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading1Tight",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=HexColor("#111111"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2Tight",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=HexColor("#111111"),
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading3Tight",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=HexColor("#111111"),
            spaceAfter=5,
        )
    )
    return styles


def inline_markup(text: str) -> str:
    escaped = html.escape(text, quote=False)
    return CODE_PLACEHOLDER.sub(
        lambda match: f'<font name="Courier" backColor="#F3F3F3">{html.escape(match.group(1), quote=False)}</font>',
        escaped,
    )


def heading_style(level: int, styles: StyleSheet1) -> ParagraphStyle:
    if level <= 1:
        return styles["Heading1Tight"]
    if level == 2:
        return styles["Heading2Tight"]
    return styles["Heading3Tight"]


def flush_paragraph(buffer: list[str], story: list, styles: StyleSheet1) -> None:
    if not buffer:
        return
    text = " ".join(part.strip() for part in buffer if part.strip())
    if text:
        story.append(Paragraph(inline_markup(text), styles["BodyTight"]))
    buffer.clear()


def flush_preformatted(buffer: list[str], story: list) -> None:
    if not buffer:
        return
    story.append(
        Preformatted(
            "\n".join(buffer),
            ParagraphStyle(
                "CodeBlock",
                fontName="Courier",
                fontSize=8.5,
                leading=10.5,
                leftIndent=10,
                rightIndent=10,
                spaceAfter=6,
                backColor=HexColor("#F6F6F6"),
            ),
        )
    )
    buffer.clear()


def render_markdown(src: Path, dest: Path) -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(dest),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=src.stem,
        author="Codex",
    )

    story: list = []
    paragraph_buffer: list[str] = []
    pre_buffer: list[str] = []
    in_code = False

    lines = src.read_text(encoding="utf-8").splitlines()
    for raw_line in lines:
        line = raw_line.rstrip("\n")

        if line.startswith("```"):
            flush_paragraph(paragraph_buffer, story, styles)
            if in_code:
                flush_preformatted(pre_buffer, story)
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            pre_buffer.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph_buffer, story, styles)
            if story and not isinstance(story[-1], Spacer):
                story.append(Spacer(1, 4))
            continue

        if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            flush_paragraph(paragraph_buffer, story, styles)
            pre_buffer.append(line)
            continue
        elif pre_buffer:
            flush_preformatted(pre_buffer, story)

        if line.startswith("#"):
            flush_paragraph(paragraph_buffer, story, styles)
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip()
            story.append(Paragraph(inline_markup(heading), heading_style(level, styles)))
            continue

        stripped = line.strip()
        if stripped.startswith("- "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(inline_markup(f"• {stripped[2:]}"), styles["BulletTight"]))
            continue

        number_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if number_match:
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(
                Paragraph(
                    inline_markup(f"{number_match.group(1)}. {number_match.group(2)}"),
                    styles["BulletTight"],
                )
            )
            continue

        paragraph_buffer.append(line)

    flush_paragraph(paragraph_buffer, story, styles)
    flush_preformatted(pre_buffer, story)
    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    for src in args.sources:
        output_dir = args.output_dir or src.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        dest = output_dir / f"{src.stem}.pdf"
        render_markdown(src, dest)
        print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
