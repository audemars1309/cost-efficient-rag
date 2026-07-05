# splits text into chunks: paragraphs first, then sentences if a paragraph
# is too long, then just cuts it if a single sentence is still too long.
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_paragraphs(text: str):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[Chunk]:
    # chunk_size/overlap are character counts, not tokens.
    # tried a few values, 800/120 worked fine on the sample docs.
    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    buf = ""

    for para in paragraphs:
        candidate = f"{buf}\n\n{para}" if buf else para
        if len(candidate) <= chunk_size:
            buf = candidate
            continue

        if buf:
            chunks.append(buf)
        if len(para) <= chunk_size:
            buf = para
        else:
            # paragraph itself too big -> split on sentences
            sentences = _SENTENCE_SPLIT.split(para)
            sbuf = ""
            for s in sentences:
                cand = f"{sbuf} {s}".strip() if sbuf else s
                if len(cand) <= chunk_size:
                    sbuf = cand
                else:
                    if sbuf:
                        chunks.append(sbuf)
                    sbuf = s[:chunk_size]  # hard cut for pathological single sentences
            buf = sbuf

    if buf:
        chunks.append(buf)

    # add overlap between chunks
    overlapped: list[str] = []
    for i, c in enumerate(chunks):
        if i == 0 or overlap <= 0:
            overlapped.append(c)
        else:
            tail = chunks[i - 1][-overlap:]
            overlapped.append(f"{tail} {c}")

    return [Chunk(text=c, index=i) for i, c in enumerate(overlapped)]
