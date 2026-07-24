from pathlib import Path

from app.chunking.chunker import chunk_pages
from app.chunking.pdf_loader import load_pdf_pages

_JLS_PDF_PATH = Path(__file__).resolve().parents[2] / "data" / "jls25.pdf"


def test_loading_and_chunking_the_real_jls_pdf_produces_sane_chunks() -> None:
    pages = load_pdf_pages(_JLS_PDF_PATH)
    assert len(pages) > 800

    chunks = chunk_pages(pages, document="jls25")

    assert len(chunks) > 400

    for index, chunk in enumerate(chunks):
        assert chunk.chunk_index == index
        assert chunk.chunk_id == f"jls25-{index}"
        assert chunk.document == "jls25"
        assert chunk.text.strip()

    headings = [chunk.text.splitlines()[0] for chunk in chunks]
    assert "Chapter 1: Introduction" in headings
    assert any(heading.startswith("4.2") for heading in headings)

    all_text = "\n".join(chunk.text for chunk in chunks)
    assert "Limited License Grant" not in all_text
