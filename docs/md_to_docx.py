#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import zipfile
from xml.sax.saxutils import escape


def parse_markdown(text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        joined = " ".join(part.strip() for part in paragraph if part.strip()).strip()
        if joined:
            blocks.append({"type": "paragraph", "text": joined, "style": "Normal"})
        paragraph = []

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if stripped == "<<<PAGE_BREAK>>>":
            flush_paragraph()
            blocks.append({"type": "page_break", "text": "", "style": "Normal"})
            continue

        if not stripped:
            flush_paragraph()
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)), 3)
            style = f"Heading{level}"
            blocks.append({"type": "heading", "text": heading.group(2).strip(), "style": style})
            continue

        if re.match(r"^(-|\d+\.)\s+", stripped):
            flush_paragraph()
            blocks.append({"type": "paragraph", "text": stripped, "style": "Normal"})
            continue

        paragraph.append(stripped)

    flush_paragraph()
    return blocks


def paragraph_xml(text: str, style: str = "Normal") -> str:
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>"
        f"<w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"
        "</w:p>"
    )


def page_break_xml() -> str:
    return "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>"


def build_document_xml(blocks: list[dict[str, str]]) -> str:
    body_parts: list[str] = []
    for block in blocks:
        if block["type"] == "page_break":
            body_parts.append(page_break_xml())
        else:
            body_parts.append(paragraph_xml(block["text"], block["style"]))

    sect_pr = (
        "<w:sectPr>"
        "<w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" "
        "w:header=\"720\" w:footer=\"720\" w:gutter=\"0\"/>"
        "<w:cols w:space=\"720\"/>"
        "<w:docGrid w:linePitch=\"360\"/>"
        "</w:sectPr>"
    )
    body = "".join(body_parts) + sect_pr
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document "
        "xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/word/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
        "mc:Ignorable=\"w14 wp14\">"
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )


def styles_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:styles xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        "<w:docDefaults>"
        "<w:rPrDefault><w:rPr>"
        "<w:rFonts w:ascii=\"Times New Roman\" w:hAnsi=\"Times New Roman\" w:cs=\"Times New Roman\"/>"
        "<w:sz w:val=\"24\"/><w:szCs w:val=\"24\"/>"
        "</w:rPr></w:rPrDefault>"
        "<w:pPrDefault><w:pPr><w:spacing w:line=\"360\" w:lineRule=\"auto\"/></w:pPr></w:pPrDefault>"
        "</w:docDefaults>"
        "<w:style w:type=\"paragraph\" w:default=\"1\" w:styleId=\"Normal\">"
        "<w:name w:val=\"Normal\"/>"
        "<w:qFormat/>"
        "<w:rPr>"
        "<w:rFonts w:ascii=\"Times New Roman\" w:hAnsi=\"Times New Roman\" w:cs=\"Times New Roman\"/>"
        "<w:sz w:val=\"24\"/><w:szCs w:val=\"24\"/>"
        "</w:rPr>"
        "<w:pPr><w:spacing w:line=\"360\" w:lineRule=\"auto\"/></w:pPr>"
        "</w:style>"
        "<w:style w:type=\"paragraph\" w:styleId=\"Heading1\">"
        "<w:name w:val=\"heading 1\"/>"
        "<w:basedOn w:val=\"Normal\"/>"
        "<w:next w:val=\"Normal\"/>"
        "<w:uiPriority w:val=\"9\"/>"
        "<w:qFormat/>"
        "<w:pPr><w:spacing w:before=\"240\" w:after=\"120\"/></w:pPr>"
        "<w:rPr><w:b/><w:sz w:val=\"28\"/><w:szCs w:val=\"28\"/></w:rPr>"
        "</w:style>"
        "<w:style w:type=\"paragraph\" w:styleId=\"Heading2\">"
        "<w:name w:val=\"heading 2\"/>"
        "<w:basedOn w:val=\"Normal\"/>"
        "<w:next w:val=\"Normal\"/>"
        "<w:uiPriority w:val=\"9\"/>"
        "<w:qFormat/>"
        "<w:pPr><w:spacing w:before=\"180\" w:after=\"100\"/></w:pPr>"
        "<w:rPr><w:b/><w:sz w:val=\"26\"/><w:szCs w:val=\"26\"/></w:rPr>"
        "</w:style>"
        "<w:style w:type=\"paragraph\" w:styleId=\"Heading3\">"
        "<w:name w:val=\"heading 3\"/>"
        "<w:basedOn w:val=\"Normal\"/>"
        "<w:next w:val=\"Normal\"/>"
        "<w:uiPriority w:val=\"9\"/>"
        "<w:qFormat/>"
        "<w:pPr><w:spacing w:before=\"120\" w:after=\"80\"/></w:pPr>"
        "<w:rPr><w:b/><w:sz w:val=\"24\"/><w:szCs w:val=\"24\"/></w:rPr>"
        "</w:style>"
        "</w:styles>"
    )


def content_types_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/word/document.xml\" "
        "ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>"
        "<Override PartName=\"/word/styles.xml\" "
        "ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml\"/>"
        "<Override PartName=\"/docProps/core.xml\" "
        "ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>"
        "<Override PartName=\"/docProps/app.xml\" "
        "ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>"
        "</Types>"
    )


def root_rels_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" "
        "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" "
        "Target=\"word/document.xml\"/>"
        "<Relationship Id=\"rId2\" "
        "Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" "
        "Target=\"docProps/core.xml\"/>"
        "<Relationship Id=\"rId3\" "
        "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" "
        "Target=\"docProps/app.xml\"/>"
        "</Relationships>"
    )


def document_rels_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" "
        "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" "
        "Target=\"styles.xml\"/>"
        "</Relationships>"
    )


def core_xml(title: str) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<cp:coreProperties "
        "xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" "
        "xmlns:dc=\"http://purl.org/dc/elements/1.1/\" "
        "xmlns:dcterms=\"http://purl.org/dc/terms/\" "
        "xmlns:dcmitype=\"http://purl.org/dc/dcmitype/\" "
        "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
        f"<dc:title>{escape(title)}</dc:title>"
        "<dc:creator>Codex</dc:creator>"
        "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
        f"<dcterms:created xsi:type=\"dcterms:W3CDTF\">{now}</dcterms:created>"
        f"<dcterms:modified xsi:type=\"dcterms:W3CDTF\">{now}</dcterms:modified>"
        "</cp:coreProperties>"
    )


def app_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" "
        "xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">"
        "<Application>Microsoft Office Word</Application>"
        "</Properties>"
    )


def build_docx(markdown_path: Path, output_path: Path) -> None:
    source = markdown_path.read_text(encoding="utf-8")
    blocks = parse_markdown(source)
    title = "Project Paper"
    for block in blocks:
        if block["type"] in {"heading", "paragraph"} and block["text"].strip():
            title = block["text"].strip()
            break

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml())
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("docProps/core.xml", core_xml(title))
        zf.writestr("docProps/app.xml", app_xml())
        zf.writestr("word/document.xml", build_document_xml(blocks))
        zf.writestr("word/styles.xml", styles_xml())
        zf.writestr("word/_rels/document.xml.rels", document_rels_xml())


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert markdown-like text to a minimal DOCX.")
    parser.add_argument("input", type=Path, help="Input markdown file")
    parser.add_argument("output", type=Path, help="Output .docx file")
    args = parser.parse_args()

    build_docx(args.input, args.output)


if __name__ == "__main__":
    main()
