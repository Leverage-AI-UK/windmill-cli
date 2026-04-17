"""Search utilities for client-side keyword matching."""

from __future__ import annotations

import json
from typing import Any


def keyword_match(
    query: str,
    text: str,
    *,
    case_sensitive: bool = False,
) -> bool:
    """Check if all space-separated query keywords are present in text.

    Uses AND logic: all keywords must match for a successful match.
    """
    if not query or not text:
        return False
    if not case_sensitive:
        query = query.lower()
        text = text.lower()
    keywords = query.split()
    return all(keyword in text for keyword in keywords)


def extract_searchable_text(item: dict[str, Any], fields: list[str]) -> str:
    """Extract text from specified fields for searching.

    Handles nested dicts/lists by JSON-serializing them.
    """
    parts: list[str] = []
    for field in fields:
        value = item.get(field)
        if value is None:
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (dict, list)):
            parts.append(json.dumps(value, ensure_ascii=False))
        else:
            parts.append(str(value))
    return " ".join(parts)


def search_items(
    items: list[dict[str, Any]],
    query: str,
    fields: list[str],
    *,
    case_sensitive: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Filter items by keyword matching across specified fields.

    Args:
        items: List of items to search.
        query: Space-separated keywords (AND logic).
        fields: List of field names to search within each item.
        case_sensitive: Whether to match case-sensitively.
        limit: Maximum number of results to return.

    Returns:
        List of matching items.
    """
    results: list[dict[str, Any]] = []
    for item in items:
        searchable = extract_searchable_text(item, fields)
        if keyword_match(query, searchable, case_sensitive=case_sensitive):
            results.append(item)
            if limit and len(results) >= limit:
                break
    return results
