"""PDF -> per-page PNG rendering via PyMuPDF (fitz).

PyMuPDF is pip-only (no system poppler dependency), which keeps the sample a
clean `pip install` on any platform. `fitz` is imported lazily inside the
function so importing the app (and running the structural / contract tests)
never requires the native wheel to be installed.
"""


def render_pdf_to_pngs(pdf_bytes: bytes, dpi: int = 150) -> list[bytes]:
    """Rasterize every page of a PDF to a PNG image.

    Returns one PNG byte-string per page, in page order. Raises RuntimeError on
    a malformed / unreadable PDF so the service layer can map it to a 400.
    """
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:  # fitz raises its own error types
        raise RuntimeError(f"Could not open PDF: {e}") from e

    # 72 is the PDF's own base DPI; the zoom scales the raster up to the target.
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    pages: list[bytes] = []
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append(pix.tobytes("png"))
    finally:
        doc.close()

    if not pages:
        raise RuntimeError("PDF has no renderable pages")
    return pages
