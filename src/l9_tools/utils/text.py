"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [utility]
tags: [text, matching]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from fnmatch import fnmatch


def normalize_words(value: str) -> set[str]:
    return {part.strip(".,:;()[]{}").lower() for part in value.split() if part.strip()}


def contains_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def path_matches_any(paths: list[str], patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for path in paths for pattern in patterns)


def stable_slug(value: str) -> str:
    cleaned: list[str] = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-") or "unknown"
