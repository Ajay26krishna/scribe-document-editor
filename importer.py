"""Dependency-free, deliberately scoped .txt / .md -> Quill Delta importer."""
from __future__ import annotations

import re

INLINE_PATTERN = re.compile(r"(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`)")


def _inline_ops(line: str) -> list[dict]:
    parts: list[dict] = []
    cursor = 0
    for m in INLINE_PATTERN.finditer(line):
        if m.start() > cursor:
            parts.append({"insert": line[cursor:m.start()]})
        token = m.group(0)
        if token.startswith("**"):
            parts.append({"insert": token[2:-2], "attributes": {"bold": True}})
        elif token.startswith("*"):
            parts.append({"insert": token[1:-1], "attributes": {"italic": True}})
        else:
            parts.append({"insert": token[1:-1], "attributes": {"code": True}})
        cursor = m.end()
    if cursor < len(line):
        parts.append({"insert": line[cursor:]})
    return parts


def to_delta(text: str, suffix: str) -> dict:
    if not text:
        return {"ops": [{"insert": "\n"}]}
    ops: list[dict] = []
    for line in text.splitlines():
        attrs: dict = {}
        content = line
        if suffix == ".md":
            heading = re.match(r"^(#{1,3})\s+(.+)$", line)
            bullet = re.match(r"^\s*[-*+]\s+(.+)$", line)
            ordered = re.match(r"^\s*\d+\.\s+(.+)$", line)
            if heading:
                attrs = {"header": len(heading.group(1))}
                content = heading.group(2)
            elif bullet:
                attrs = {"list": "bullet"}
                content = bullet.group(1)
            elif ordered:
                attrs = {"list": "ordered"}
                content = ordered.group(1)
        if suffix == ".md":
            ops.extend(_inline_ops(content))
        elif content:
            ops.append({"insert": content})
        ops.append({"insert": "\n", **({"attributes": attrs} if attrs else {})})
    return {"ops": ops or [{"insert": "\n"}]}
