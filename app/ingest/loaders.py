"""Load local HTML, Markdown, text, and PDF sources into normalized text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LoadedPage:
    text: str
    page: int | None = None


@dataclass(frozen=True)
class LoadedDocument:
    source: str
    title: str
    doc_type: str
    pages: tuple[LoadedPage, ...]


SUPPORTED_SUFFIXES = {".html", ".htm", ".md", ".txt", ".pdf"}


def normalize_text(value: str) -> str:
    """Normalize accents and whitespace while keeping paragraph boundaries."""
    value = unicodedata.normalize("NFC", value.replace("\xa0", " ").replace("\r\n", "\n"))
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in value.splitlines()]
    normalized = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", normalized).strip()


def _title_from_text(text: str, path: Path) -> str:
    for line in text.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*#*\s*$", line)
        if match:
            return match.group(1).strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def load_document(path: str | Path, *, source: str | None = None) -> LoadedDocument:
    """Load one supported file; PDF pages remain separate for citations."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported document type: {suffix}")
    display_source = source or file_path.as_posix()

    if suffix == ".pdf":
        import pymupdf

        with pymupdf.open(file_path) as pdf:
            pages_list = []
            for index, page in enumerate(pdf, start=1):
                text = normalize_text(page.get_text("text"))
                if text:
                    pages_list.append(LoadedPage(text, page=index))
            pages = tuple(pages_list)
        if not pages:
            raise ValueError(f"PDF contains no extractable text: {file_path}")
        title = _title_from_text(pages[0].text, file_path)
        return LoadedDocument(display_source, title, "pdf", pages)

    raw = file_path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".html", ".htm"}:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")
        for element in soup.select("nav, footer, script, style, noscript"):
            element.decompose()
        title_node = soup.find("title") or soup.find(["h1", "h2"])
        title = normalize_text(title_node.get_text(" ", strip=True)) if title_node else ""
        content = normalize_text(soup.get_text("\n", strip=True))
    else:
        content = normalize_text(raw)
        title = ""
    title = title or _title_from_text(content, file_path)
    if not content:
        raise ValueError(f"Document contains no extractable text: {file_path}")
    return LoadedDocument(display_source, title, "html" if suffix in {".html", ".htm"} else "text", (LoadedPage(content),))
