"""Lightweight Day 10 data pipeline corpus service.

The original Day 10 project builds Chroma indexes and evaluation artifacts. For
cloud deployment we ship the generated artifacts and use a small lexical search
layer so the service stays fast to build on Railway.
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "day10_artifacts"


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
        if token not in {"the", "and", "for", "with", "this", "that", "from"}
    }


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0] if parts and parts[0] else text[:280]


@lru_cache(maxsize=1)
def load_papers() -> list[dict[str, Any]]:
    return _read_json(ARTIFACT_DIR / "clean" / "papers_clean.json", [])


@lru_cache(maxsize=1)
def load_metrics() -> dict[str, Any]:
    return {
        "baseline": _read_json(ARTIFACT_DIR / "results" / "baseline_metrics.json", {}),
        "corrupted": _read_json(ARTIFACT_DIR / "results" / "corrupted_metrics.json", {}),
        "repaired": _read_json(ARTIFACT_DIR / "results" / "repaired_metrics.json", {}),
    }


@lru_cache(maxsize=1)
def load_quality() -> dict[str, Any]:
    return {
        "baseline_quality": _read_json(ARTIFACT_DIR / "quality" / "baseline_quality.json", {}),
        "freshness": _read_json(ARTIFACT_DIR / "quality" / "freshness_report.json", {}),
    }


def corpus_summary() -> dict[str, Any]:
    papers = load_papers()
    quality = load_quality()
    return {
        "source": "Day-10-Data-Pipeline-Data-Observability",
        "paper_count": len(papers),
        "metrics": load_metrics(),
        "quality": {
            "overall_status": "PASS" if quality["baseline_quality"].get("passed") else "FAIL",
            "total_rows": quality["baseline_quality"].get("total_rows"),
            "failed_checks": quality["baseline_quality"].get("failed_checks", 0),
            "freshness": quality["freshness"],
        },
    }


def search_papers(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scored = []
    for paper in load_papers():
        haystack = " ".join(
            str(paper.get(field, ""))
            for field in ("title", "summary", "authors_joined", "categories_joined")
        )
        haystack_tokens = _tokens(haystack)
        overlap = len(query_tokens & haystack_tokens)
        title_bonus = 2 if query.lower() in str(paper.get("title", "")).lower() else 0
        score = overlap + title_bonus
        if score > 0:
            scored.append((score, paper))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "paper_id": paper.get("paper_id"),
            "title": paper.get("title"),
            "authors": paper.get("authors_joined"),
            "published": paper.get("published"),
            "score": score,
            "summary": paper.get("summary"),
            "url": paper.get("abs_url"),
        }
        for score, paper in scored[:top_k]
    ]


def answer_from_corpus(question: str) -> dict[str, Any]:
    matches = search_papers(question, top_k=3)
    if not matches:
        return {
            "answer": "I could not find a matching paper in the Day 10 indexed corpus.",
            "matches": [],
        }

    top = matches[0]
    lowered = question.lower()
    if "author" in lowered or "who wrote" in lowered:
        answer = f"The closest matching paper is '{top['title']}', authored by {top['authors']}."
    elif "published" in lowered or "when" in lowered:
        answer = f"The closest matching paper is '{top['title']}', published on {top['published']}."
    else:
        answer = (
            f"Based on the Day 10 cleaned corpus, the closest paper is '{top['title']}'. "
            f"{_first_sentence(str(top.get('summary', '')))}"
        )

    return {
        "answer": answer,
        "matches": matches,
    }


def load_report(name: str) -> dict[str, str]:
    report_map = {
        "phase1": ARTIFACT_DIR / "reports" / "phase1_report.md",
        "corruption": ARTIFACT_DIR / "reports" / "corruption_report.md",
    }
    path = report_map.get(name)
    if not path or not path.exists():
        return {"name": name, "content": "Report not found."}
    return {"name": name, "content": path.read_text(encoding="utf-8")}
