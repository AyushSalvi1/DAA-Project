"""Corpus loading and seeding.

Responsibilities
----------------
* merge the three corpus parts into one ordered document list,
* mirror every document to ``data/sample_documents/*.txt`` (plain text files
  a user can inspect or re-import through the admin importer),
* insert everything into SQLite on first run, marking duplicates by slug so
  re-seeding is safe,
* build the index, the graph and the TF-IDF model.
"""

from __future__ import annotations

import os
from typing import Any

from core.corpus_part1 import ARTICLES as PART1
from core.corpus_part2 import ARTICLES as PART2
from core.corpus_part3 import ARTICLES as PART3

ARTICLES: list[dict] = [*PART1, *PART2, *PART3]
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "sample_documents")
DEFAULT_ADMIN = {"username": "admin", "password": "nexasearch123", "role": "admin"}


def _keywords(raw: str) -> list[str]:
    return [k.strip() for k in (raw or "").split(",") if k.strip()]


def articles_as_documents() -> list[dict[str, Any]]:
    """Normalise the raw articles into the shape the indexer expects."""
    documents = []
    for article in ARTICLES:
        keywords = _keywords(article["keywords"])
        summary = article["content"].strip().split("\n\n")[0]
        documents.append({
            "title": article["title"],
            "slug": article["slug"],
            "content": article["content"],
            "summary": summary[:300],
            "category": article["category"],
            "author": article["author"],
            "url": article["url"],
            "keywords": keywords,
        })
    return documents


def write_sample_files(directory: str = SAMPLE_DIR) -> int:
    """Write each article to ``data/sample_documents/<slug>.txt``."""
    os.makedirs(directory, exist_ok=True)
    written = 0
    for document in articles_as_documents():
        path = os.path.join(directory, f"{document['slug']}.txt")
        body = (
            f"TITLE: {document['title']}\n"
            f"CATEGORY: {document['category']}\n"
            f"AUTHOR: {document['author']}\n"
            f"KEYWORDS: {', '.join(document['keywords'])}\n"
            f"SUMMARY: {document['summary']}\n"
            f"{'-' * 70}\n\n"
            f"{document['content']}\n"
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        written += 1
    return written


def seed_database(db, force: bool = False) -> dict:
    """Populate an empty database (or add missing articles)."""
    if db.is_empty() and not force:
        pass  # normal first-run path
    existing_slugs = {row["slug"] for row in db.query("SELECT slug FROM documents")}
    inserted = 0
    skipped = 0
    db.defer_keyword_stats = True
    try:
        for document in articles_as_documents():
            if document["slug"] in existing_slugs:
                skipped += 1
                continue
            try:
                db.add_document(
                    title=document["title"],
                    content=document["content"],
                    category=document["category"],
                    author=document["author"],
                    url=document["url"],
                    keywords=document["keywords"],
                    summary=document["summary"],
                    slug=document["slug"],
                )
                inserted += 1
            except ValueError:
                skipped += 1
    finally:
        db.defer_keyword_stats = False
        if inserted:
            db.recompute_keyword_stats()
    if not db.user_count():
        db.ensure_user(DEFAULT_ADMIN["username"], DEFAULT_ADMIN["password"],
                       DEFAULT_ADMIN["role"])
    files = write_sample_files()
    return {
        "inserted": inserted,
        "skipped": skipped,
        "sample_files": files,
        "total_articles": len(ARTICLES),
        "demo_admin": DEFAULT_ADMIN,
    }


def import_text_file(db, filename: str, content: str) -> int:
    """Import one ``.txt`` document, parsing the optional header block."""
    title = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").replace("-", " ").title()
    category = "Uncategorised"
    author = "Imported Document"
    keywords: list[str] = []
    summary = ""

    lines = content.splitlines()
    body_start = 0
    for index, line in enumerate(lines[:10]):
        upper = line.strip().upper()
        if upper.startswith("TITLE:"):
            title = line.split(":", 1)[1].strip() or title
            body_start = index + 1
        elif upper.startswith("CATEGORY:"):
            category = line.split(":", 1)[1].strip() or category
            body_start = index + 1
        elif upper.startswith("AUTHOR:"):
            author = line.split(":", 1)[1].strip() or author
            body_start = index + 1
        elif upper.startswith("KEYWORDS:"):
            keywords = [k.strip() for k in line.split(":", 1)[1].split(",") if k.strip()]
            body_start = index + 1
        elif upper.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
            body_start = index + 1
        elif set(line.strip()) == {"-"} and line.strip():
            body_start = index + 1
            break

    body = "\n".join(lines[body_start:]).strip() or content.strip()
    if not keywords:
        from indexing.text_processor import keywords_from_text
        keywords = keywords_from_text(body, limit=6)
    return db.add_document(title=title, content=body, category=category,
                           author=author, keywords=keywords, summary=summary)
