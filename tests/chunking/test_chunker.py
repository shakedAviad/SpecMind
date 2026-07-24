import re

from app.chunking.chunker import chunk_pages


def test_front_matter_before_first_chapter_is_skipped() -> None:
    pages = [
        "The Java (R) Language Specification\n1.1 Organization 45\n1.2 Example 46",
        "CHAPTER 1\nIntroduction\nTHE first chapter body begins here and continues for a while.",
    ]

    chunks = chunk_pages(pages, document="jls")

    assert len(chunks) == 1
    assert chunks[0].text.startswith("Chapter 1: Introduction")
    assert "Organization" not in chunks[0].text


def test_chapter_title_spanning_multiple_lines_is_joined() -> None:
    pages = [
        "CHAPTER 14\nBlocks, Statements, and\nPatterns\nTHE body starts here with real content.",
    ]

    chunks = chunk_pages(pages, document="jls")

    assert chunks[0].text.startswith("Chapter 14: Blocks, Statements, and Patterns")


def test_section_and_subsection_headings_split_into_separate_chunks() -> None:
    pages = [
        "CHAPTER 1\nIntroduction\nTHE opening paragraph of the chapter.",
        "1.2 Example Programs INTRODUCTION\n"
        "1.2 Example Programs\n"
        "Body text describing example programs.\n"
        "1.3 Notation\n"
        "Body text describing notation.\n"
        "6",
    ]

    chunks = chunk_pages(pages, document="jls")

    headings = [chunk.text.splitlines()[0] for chunk in chunks]
    assert "Chapter 1: Introduction" in headings
    assert "1.2 Example Programs" in headings
    assert "1.3 Notation" in headings

    example_chunk = next(c for c in chunks if c.text.startswith("1.2 Example Programs"))
    assert "describing example programs" in example_chunk.text
    assert "Notation" not in example_chunk.text.split("\n\n", 1)[1]


def test_running_header_and_page_number_footer_are_stripped() -> None:
    pages = [
        "CHAPTER 3\nLexical Structure\nTHE opening paragraph.",
        "3.6 White Space LEXICAL STRUCTURE\n3.6 White Space\nWhite space content goes here.\n26",
    ]

    chunks = chunk_pages(pages, document="jls")

    white_space_chunk = next(c for c in chunks if c.text.startswith("3.6 White Space"))
    assert "LEXICAL STRUCTURE" not in white_space_chunk.text
    assert "26" not in white_space_chunk.text


def test_content_after_appendix_heading_is_excluded() -> None:
    pages = [
        "CHAPTER 1\nIntroduction\nTHE opening paragraph of the chapter.",
        "Appendix A. Limited License Grant\nORACLE AMERICA legal text.",
        "CHAPTER 1\nIntroduction\nThis should never be reached.",
    ]

    chunks = chunk_pages(pages, document="jls")

    assert len(chunks) == 1
    assert "legal text" not in chunks[0].text
    assert "never be reached" not in chunks[0].text


def test_oversized_section_is_split_into_multiple_chunks_without_exceeding_limit() -> None:
    sentence = "This is one sentence about Java generics and type erasure. "
    long_body = "THE " + sentence * 80
    pages = [f"CHAPTER 1\nIntroduction\n{long_body}"]

    chunks = chunk_pages(pages, document="jls")

    assert len(chunks) > 1
    for chunk in chunks:
        paragraph = chunk.text.split("\n\n", 1)[1]
        assert len(paragraph) <= 1500 + 3 * len(sentence)


def test_oversized_section_subchunks_overlap_by_the_trailing_sentences() -> None:
    sentence = "This is one sentence about Java generics and type erasure. "
    long_body = "THE " + sentence * 80
    pages = [f"CHAPTER 1\nIntroduction\n{long_body}"]

    chunks = chunk_pages(pages, document="jls")

    assert len(chunks) > 1
    for previous, current in zip(chunks, chunks[1:], strict=False):
        previous_paragraph = previous.text.split("\n\n", 1)[1]
        current_paragraph = current.text.split("\n\n", 1)[1]
        previous_sentences = re.split(r"(?<=[.!?])\s+", previous_paragraph.strip())
        current_sentences = re.split(r"(?<=[.!?])\s+", current_paragraph.strip())
        assert current_sentences[:2] == previous_sentences[-2:]


def test_chunk_index_and_chunk_id_are_sequential() -> None:
    sentence = "This is one sentence about Java generics and type erasure. "
    long_body = "THE " + sentence * 80
    pages = [f"CHAPTER 1\nIntroduction\n{long_body}"]

    chunks = chunk_pages(pages, document="jls")

    for expected_index, chunk in enumerate(chunks):
        assert chunk.chunk_index == expected_index
        assert chunk.chunk_id == f"jls-{expected_index}"
        assert chunk.document == "jls"


def test_heading_with_no_body_text_produces_no_chunk() -> None:
    pages = [
        "CHAPTER 1\nIntroduction\nTHE opening paragraph.",
        "1.2 Example Programs INTRODUCTION\n1.2 Example Programs\n1.3 Notation\nReal body text.\n6",
    ]

    chunks = chunk_pages(pages, document="jls")

    headings = [chunk.text.splitlines()[0] for chunk in chunks]
    assert "1.2 Example Programs" not in headings
    assert "1.3 Notation" in headings
