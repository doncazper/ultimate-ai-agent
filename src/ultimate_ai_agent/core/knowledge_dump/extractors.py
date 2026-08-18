from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote
import zipfile
import xml.etree.ElementTree as ET

from ultimate_ai_agent.core.knowledge_dump.models import KnowledgeFormat


MAX_SOURCE_BYTES = 100 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 20_000_000
MAX_EPUB_ENTRIES = 10_000


@dataclass(frozen=True)
class ExtractedSection:
    locator: str
    text: str


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif not self._ignored_depth and tag in {
            "p",
            "div",
            "br",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
        }:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif not self._ignored_depth and tag in {
            "p",
            "div",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
        }:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)

    def text(self) -> str:
        return _normalize_text("".join(self.parts))


def detect_format(path: Path) -> KnowledgeFormat:
    suffix = path.suffix.lower()
    mapping = {
        ".txt": KnowledgeFormat.plain_text,
        ".md": KnowledgeFormat.markdown,
        ".markdown": KnowledgeFormat.markdown,
        ".html": KnowledgeFormat.html,
        ".htm": KnowledgeFormat.html,
        ".epub": KnowledgeFormat.epub,
    }
    if suffix not in mapping:
        raise ValueError("KNOWLEDGE_SOURCE_FORMAT_UNSUPPORTED")
    return mapping[suffix]


def extract_sections(
    path: Path, source_format: KnowledgeFormat
) -> list[ExtractedSection]:
    if not path.is_file():
        raise ValueError("KNOWLEDGE_SOURCE_FILE_REQUIRED")
    size = path.stat().st_size
    if size <= 0 or size > MAX_SOURCE_BYTES:
        raise ValueError("KNOWLEDGE_SOURCE_SIZE_OUT_OF_BOUNDS")
    if source_format in {KnowledgeFormat.plain_text, KnowledgeFormat.markdown}:
        sections = _extract_text(path)
    elif source_format == KnowledgeFormat.html:
        sections = _extract_html(path)
    elif source_format == KnowledgeFormat.epub:
        sections = _extract_epub(path)
    else:
        raise ValueError("KNOWLEDGE_SOURCE_FORMAT_UNSUPPORTED")
    total = sum(len(section.text) for section in sections)
    if not sections or total <= 0:
        raise ValueError("KNOWLEDGE_SOURCE_HAS_NO_EXTRACTABLE_TEXT")
    if total > MAX_EXTRACTED_CHARACTERS:
        raise ValueError("KNOWLEDGE_EXTRACTED_TEXT_OUT_OF_BOUNDS")
    return sections


def _extract_text(path: Path) -> list[ExtractedSection]:
    text = _read_utf8_text(path)
    lines = text.splitlines()
    sections: list[ExtractedSection] = []
    start = 1
    buffer: list[str] = []
    for number, line in enumerate(lines, 1):
        if not line.strip() and buffer:
            sections.append(
                ExtractedSection(
                    f"lines:{start}-{number - 1}", _normalize_text("\n".join(buffer))
                )
            )
            buffer = []
            start = number + 1
        elif line.strip():
            if not buffer:
                start = number
            buffer.append(line)
    if buffer:
        sections.append(
            ExtractedSection(
                f"lines:{start}-{len(lines)}", _normalize_text("\n".join(buffer))
            )
        )
    return [section for section in sections if section.text]


def _extract_html(path: Path) -> list[ExtractedSection]:
    parser = _TextHTMLParser()
    parser.feed(_read_utf8_text(path))
    return [ExtractedSection("document", parser.text())]


def _extract_epub(path: Path) -> list[ExtractedSection]:
    try:
        return _extract_epub_archive(path)
    except zipfile.BadZipFile as exc:
        raise ValueError("KNOWLEDGE_EPUB_ARCHIVE_INVALID") from exc


def _extract_epub_archive(path: Path) -> list[ExtractedSection]:
    sections: list[ExtractedSection] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if (
            len(infos) > MAX_EPUB_ENTRIES
            or sum(info.file_size for info in infos) > MAX_SOURCE_BYTES
        ):
            raise ValueError("KNOWLEDGE_EPUB_ARCHIVE_OUT_OF_BOUNDS")
        names = _epub_spine_names(archive)
        for ordinal, name in enumerate(names, 1):
            parser = _TextHTMLParser()
            parser.feed(archive.read(name).decode("utf-8", errors="replace"))
            text = parser.text()
            if text:
                sections.append(ExtractedSection(f"epub-section:{ordinal}", text))
    return sections


def _read_utf8_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("KNOWLEDGE_SOURCE_ENCODING_UNSUPPORTED") from exc
    except OSError as exc:
        raise ValueError("KNOWLEDGE_SOURCE_READ_FAILED") from exc


def _epub_spine_names(archive: zipfile.ZipFile) -> list[str]:
    try:
        container_root = ET.fromstring(archive.read("META-INF/container.xml"))
        package_path = next(
            element.attrib["full-path"]
            for element in container_root.iter()
            if element.tag.rsplit("}", 1)[-1] == "rootfile"
            and element.attrib.get("full-path")
        )
        package_root = ET.fromstring(archive.read(package_path))
    except (KeyError, StopIteration, ET.ParseError) as exc:
        raise ValueError("KNOWLEDGE_EPUB_PACKAGE_INVALID") from exc

    manifest: dict[str, tuple[str, str]] = {}
    spine_ids: list[str] = []
    for element in package_root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name == "item":
            item_id = element.attrib.get("id")
            href = element.attrib.get("href")
            if item_id and href:
                manifest[item_id] = (href, element.attrib.get("media-type", ""))
        elif local_name == "itemref" and element.attrib.get("idref"):
            spine_ids.append(element.attrib["idref"])
    if not spine_ids:
        raise ValueError("KNOWLEDGE_EPUB_SPINE_REQUIRED")

    package_dir = posixpath.dirname(package_path)
    archive_names = set(archive.namelist())
    names: list[str] = []
    for item_id in spine_ids:
        item = manifest.get(item_id)
        if item is None:
            raise ValueError("KNOWLEDGE_EPUB_SPINE_ITEM_MISSING")
        href, media_type = item
        if media_type not in {"application/xhtml+xml", "text/html"}:
            continue
        name = posixpath.normpath(
            posixpath.join(package_dir, unquote(href.split("#", 1)[0]))
        )
        if name.startswith("../") or name.startswith("/") or name not in archive_names:
            raise ValueError("KNOWLEDGE_EPUB_SPINE_ITEM_INVALID")
        names.append(name)
    if not names:
        raise ValueError("KNOWLEDGE_EPUB_SPINE_HAS_NO_TEXT")
    return names


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
