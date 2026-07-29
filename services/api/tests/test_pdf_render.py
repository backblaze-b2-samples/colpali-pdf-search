"""Real PyMuPDF rendering test. Generates a tiny in-memory PDF with fitz, then
renders it to PNGs — no fixture files, no network."""

import fitz

from app.repo.pdf_render import render_pdf_to_pngs

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _tiny_pdf(pages: int) -> bytes:
    doc = fitz.open()
    for n in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {n + 1}")
    return doc.tobytes()


def test_render_two_page_pdf():
    pngs = render_pdf_to_pngs(_tiny_pdf(2), dpi=72)
    assert len(pngs) == 2
    for png in pngs:
        assert png[:8] == PNG_MAGIC


def test_render_rejects_non_pdf():
    import pytest

    with pytest.raises(RuntimeError):
        render_pdf_to_pngs(b"not a pdf", dpi=72)
