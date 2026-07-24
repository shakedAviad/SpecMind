from pathlib import Path

from app.chunking.chunker import chunk_pages
from app.chunking.pdf_loader import load_pdf_pages
from app.retrieval.bm25_search import Bm25Search

_JLS_PDF_PATH = Path(__file__).resolve().parents[3] / "jls25.pdf"


def test_bm25_search_ranks_the_matching_jls_section_first() -> None:
    pages = load_pdf_pages(_JLS_PDF_PATH)
    chunks = chunk_pages(pages, document="jls25")

    bm25_search = Bm25Search()
    bm25_search.index(chunks)

    results = bm25_search.search("generic type erasure", limit=3)

    assert results
    assert results[0].text.splitlines()[0].startswith("4.6 Type Erasure")
    assert all(result.score is not None for result in results)
