import re
from dataclasses import dataclass, field

from app.models.retrieval import RetrievedChunk

_MAX_CHUNK_CHARS = 1500
_OVERLAP_SENTENCES = 2

_CHAPTER_HEADING = re.compile(r"^CHAPTER\s+(\d{1,2})\s*$")
_APPENDIX_HEADING = re.compile(r"^Appendix\s+[A-Z]\.")
_SECTION_HEADING = re.compile(r"^(\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,2})\.?\s+([A-Z].{0,90})$")
_CHAPTER_BODY_START = re.compile(r"^[A-Z]{2,}\b")


@dataclass
class _Section:
    heading: str
    lines: list[str] = field(default_factory=list)


def chunk_pages(pages: list[str], document: str) -> list[RetrievedChunk]:
    sections = _split_into_sections(pages)

    chunks: list[RetrievedChunk] = []
    for section in sections:
        text = " ".join(section.lines).strip()
        if not text:
            continue

        for paragraph in _split_oversized(text):
            chunk_index = len(chunks)
            chunks.append(
                RetrievedChunk(
                    chunk_id=f"{document}-{chunk_index}",
                    document=document,
                    chunk_index=chunk_index,
                    text=f"{section.heading}\n\n{paragraph}",
                )
            )

    return chunks


def _split_into_sections(pages: list[str]) -> list[_Section]:
    sections: list[_Section] = []
    current: _Section | None = None
    started = False

    for page in pages:
        lines = [line.strip() for line in page.split("\n") if line.strip()]
        if not lines:
            continue

        if _APPENDIX_HEADING.match(lines[0]):
            break

        chapter_match = _CHAPTER_HEADING.match(lines[0])
        if chapter_match:
            started = True
            current = _Section(heading=_chapter_heading(chapter_match.group(1), lines))
            sections.append(current)
            body_lines = lines[_chapter_title_line_count(lines) :]
        elif started:
            body_lines = _strip_running_header_and_footer(lines)
        else:
            continue

        for line in body_lines:
            heading_match = _SECTION_HEADING.match(line)
            if heading_match:
                current = _Section(heading=heading_match.group(0))
                sections.append(current)
            elif current is not None:
                current.lines.append(line)

    return sections


def _chapter_title_line_count(lines: list[str]) -> int:
    body_start = 1
    for line in lines[1:4]:
        if _CHAPTER_BODY_START.match(line):
            break
        body_start += 1
    return body_start


def _chapter_heading(chapter_number: str, lines: list[str]) -> str:
    title_line_count = _chapter_title_line_count(lines)
    title = " ".join(lines[1:title_line_count])
    return f"Chapter {chapter_number}: {title}"


def _strip_running_header_and_footer(lines: list[str]) -> list[str]:
    body_lines = lines[1:]
    if body_lines and body_lines[-1].isdigit():
        body_lines = body_lines[:-1]
    return body_lines


def _split_oversized(text: str) -> list[str]:
    if len(text) <= _MAX_CHUNK_CHARS:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    groups: list[list[str]] = []
    current_sentences: list[str] = []
    current_len = 0

    for sentence in sentences:
        if current_sentences and current_len + len(sentence) > _MAX_CHUNK_CHARS:
            groups.append(current_sentences)
            current_sentences = []
            current_len = 0
        current_sentences.append(sentence)
        current_len += len(sentence) + 1

    if current_sentences:
        groups.append(current_sentences)

    return _apply_overlap(groups)


def _apply_overlap(groups: list[list[str]]) -> list[str]:
    paragraphs: list[str] = []

    for index, group in enumerate(groups):
        if index == 0:
            paragraphs.append(" ".join(group))
            continue

        overlap = groups[index - 1][-_OVERLAP_SENTENCES:]
        paragraphs.append(" ".join([*overlap, *group]))

    return paragraphs
