"""Deterministic skill taxonomy: normalization, aliasing, and categorization.

Loads data/skills/*.json (canonical skill -> alias list, grouped by category)
and builds a case-insensitive lookup from any known alias/spelling to its
canonical name. This is intentionally rule-based, not LLM-based: skill
normalization has a small, stable vocabulary and does not require semantic
reasoning, so a deterministic lookup is faster, cheaper, and fully auditable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings


@dataclass
class SkillEntry:
    canonical: str
    category: str
    aliases: list[str] = field(default_factory=list)


class SkillTaxonomy:
    """In-memory index of canonical skills, aliases, and categories."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._entries: dict[str, SkillEntry] = {}  # canonical -> entry
        self._alias_to_canonical: dict[str, str] = {}  # normalized alias -> canonical
        self._load()

    @staticmethod
    def _normalize_key(text: str) -> str:
        text = text.strip().lower()
        text = re.sub(r"[.\-_/]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _load(self) -> None:
        if not self.data_dir.exists():
            return
        for path in sorted(self.data_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            category = payload.get("category", path.stem)
            for skill in payload.get("skills", []):
                canonical = skill["canonical"]
                aliases = skill.get("aliases", [])
                entry = SkillEntry(canonical=canonical, category=category, aliases=aliases)
                self._entries[canonical] = entry
                self._alias_to_canonical[self._normalize_key(canonical)] = canonical
                for alias in aliases:
                    self._alias_to_canonical[self._normalize_key(alias)] = canonical

    def normalize(self, raw_skill: str) -> str | None:
        """Return the canonical skill name for a raw string, or None if unknown."""
        key = self._normalize_key(raw_skill)
        return self._alias_to_canonical.get(key)

    def normalize_many(self, raw_skills: list[str]) -> list[str]:
        """Normalize a list of raw skill strings, deduplicated, dropping unknowns."""
        seen: list[str] = []
        for raw in raw_skills:
            canonical = self.normalize(raw)
            if canonical and canonical not in seen:
                seen.append(canonical)
        return seen

    def category_of(self, canonical_skill: str) -> str | None:
        entry = self._entries.get(canonical_skill)
        return entry.category if entry else None

    def all_canonical_skills(self) -> list[str]:
        return list(self._entries.keys())

    def extract_from_text(self, text: str) -> list[str]:
        """Scan free text for any known skill alias (longest-match, word-boundary)."""
        found: set[str] = set()
        lowered = f" {self._normalize_key(text)} "
        # sort by length desc so multi-word aliases ("machine learning") win over
        # a substring alias that might also match ("learning")
        for alias_key, canonical in sorted(
            self._alias_to_canonical.items(), key=lambda kv: -len(kv[0])
        ):
            if not alias_key:
                continue
            pattern = r"(?<![a-z0-9])" + re.escape(alias_key) + r"(?![a-z0-9])"
            if re.search(pattern, lowered):
                found.add(canonical)
        return sorted(found)


@lru_cache
def get_skill_taxonomy() -> SkillTaxonomy:
    settings = get_settings()
    return SkillTaxonomy(settings.skills_data_dir)
