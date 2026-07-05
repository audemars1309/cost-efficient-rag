# pulls plain text out of pdf/html/md files
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
import markdown as md_lib


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def load_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def load_md(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # Render to HTML then strip tags, so headers/lists/emphasis don't pollute
    # the text with markdown syntax noise.
    html = md_lib.markdown(raw)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


LOADERS = {
    ".pdf": load_pdf,
    ".html": load_html,
    ".htm": load_html,
    ".md": load_md,
    ".markdown": load_md,
}


def load_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in LOADERS:
        raise ValueError(f"Unsupported file type: {ext} ({path})")
    return LOADERS[ext](path)


def discover_corpus(root: str):
    """Yield every ingestible file under root."""
    root_path = Path(root)
    for ext in LOADERS:
        yield from root_path.rglob(f"*{ext}")
