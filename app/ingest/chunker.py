"""Heading-aware chunking with a word-count token approximation."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_index: int
    heading: str
    text: str
    page: int | None = None


HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ0-9«(])")
WORD_RE = re.compile(r"\S+")


def approximate_tokens(text: str) -> int:
    """Use whitespace-delimited words as a simple, documented token estimate."""
    return len(WORD_RE.findall(text))


def _heading_sections(text: str) -> list[tuple[str, str]]:
    stack: list[tuple[int, str]] = []
    sections: list[tuple[str, list[str]]] = []
    current_heading = ""
    body: list[str] = []

    def save() -> None:
        nonlocal body
        content = "\n".join(body).strip()
        if content:
            sections.append((current_heading, [content]))
        body = []

    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            save()
            level = len(match.group(1))
            label = match.group(2).strip()
            stack = [(depth, name) for depth, name in stack if depth < level]
            stack.append((level, label))
            current_heading = " > ".join(name for _, name in stack)
        else:
            body.append(line)
    save()
    return [(heading, chunks[0]) for heading, chunks in sections]


def _split_long_sentence(sentence: str, max_tokens: int) -> list[str]:
    words = sentence.split()
    return [" ".join(words[index : index + max_tokens]) for index in range(0, len(words), max_tokens)]


def _sentences(paragraph: str, max_tokens: int) -> list[str]:
    sentences = [part.strip() for part in SENTENCE_RE.split(paragraph.strip()) if part.strip()]
    if not sentences:
        return []
    result: list[str] = []
    for sentence in sentences:
        if approximate_tokens(sentence) > max_tokens:
            result.extend(_split_long_sentence(sentence, max_tokens))
        else:
            result.append(sentence)
    return result


def _chunk_section(text: str, target_tokens: int, max_tokens: int, overlap_ratio: float) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    sentences = [sentence for paragraph in paragraphs for sentence in _sentences(paragraph, max_tokens)]
    if not sentences:
        sentences = [" ".join(text.split())]

    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for sentence in sentences:
        sentence_count = approximate_tokens(sentence)
        if current and count + sentence_count > target_tokens:
            chunks.append(" ".join(current))
            overlap_words = min(int(target_tokens * overlap_ratio), max_tokens - sentence_count)
            overlap = " ".join(" ".join(current).split()[-overlap_words:]) if overlap_words else ""
            current = [overlap] if overlap else []
            count = approximate_tokens(overlap)
        if sentence_count > max_tokens:
            sentence = " ".join(sentence.split()[:max_tokens])
            sentence_count = max_tokens
        if current and count + sentence_count > max_tokens:
            chunks.append(" ".join(current))
            current, count = [], 0
        current.append(sentence)
        count += sentence_count
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_text(
    text: str,
    *,
    title: str,
    target_tokens: int = 350,
    max_tokens: int = 500,
    overlap_ratio: float = 0.12,
    page: int | None = None,
) -> list[Chunk]:
    """Split text at headings then sentence boundaries, preserving section paths."""
    if target_tokens < 1 or max_tokens < target_tokens:
        raise ValueError("Require 1 <= target_tokens <= max_tokens")
    if not 0 <= overlap_ratio < 0.5:
        raise ValueError("overlap_ratio must be between 0 and 0.5")

    chunks: list[Chunk] = []
    for heading, section in _heading_sections(text):
        heading_path = heading or title
        embedded_prefix = f"Titre : {title}\nSection : {heading_path}\n"
        prefix_tokens = approximate_tokens(embedded_prefix)
        body_max = max(1, max_tokens - prefix_tokens)
        body_target = max(1, target_tokens - prefix_tokens)
        for body in _chunk_section(section, body_target, body_max, overlap_ratio):
            chunks.append(
                Chunk(
                    chunk_index=len(chunks),
                    heading=heading_path,
                    text=embedded_prefix + body,
                    page=page,
                )
            )
    if not chunks and text.strip():
        heading_path = title
        embedded_prefix = f"Titre : {title}\nSection : {heading_path}\n"
        prefix_tokens = approximate_tokens(embedded_prefix)
        body_max = max(1, max_tokens - prefix_tokens)
        body_target = max(1, target_tokens - prefix_tokens)
        for body in _chunk_section(text, body_target, body_max, overlap_ratio):
            chunks.append(Chunk(len(chunks), heading_path, embedded_prefix + body, page))
    return chunks
