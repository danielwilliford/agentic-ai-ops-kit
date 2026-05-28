from __future__ import annotations

from pathlib import Path
from app.models import RetrievedSource

DOC_DIR = Path(__file__).resolve().parent.parent / "demo_data" / "policies"


def _tokens(text: str) -> set[str]:
    punctuation = ".,:;!?()[]{}\"'"
    return {t.strip(punctuation).lower() for t in text.split() if len(t.strip(punctuation)) > 2}


def load_documents() -> list[tuple[str, str, str]]:
    docs = []
    for path in sorted(DOC_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ") if text.splitlines() else path.stem
        docs.append((path.stem, title, text))
    return docs


def retrieve(query: str, limit: int = 3) -> list[RetrievedSource]:
    q = _tokens(query)
    scored = []
    for source_id, title, text in load_documents():
        toks = _tokens(text)
        overlap = len(q & toks)
        score = min(1.0, overlap / max(6, len(q)))
        if score > 0:
            excerpt = " ".join(text.split()[:80])
            scored.append(RetrievedSource(source_id=source_id, title=title, excerpt=excerpt, score=round(score, 3)))
    return sorted(scored, key=lambda s: s.score, reverse=True)[:limit]
