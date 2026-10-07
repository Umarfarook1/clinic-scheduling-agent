"""The policy book: the part of the agent the improvement loop is allowed to change.

A policy is a persona plus a short list of numbered rules, each with an id and a record of
where it came from. Versions are plain YAML files with a parent, so every rule in the prompt
can be traced back to the eval failure that produced it, and any version can be diffed or
rolled back. The loop never rewrites the prompt wholesale; it adds, edits or removes rules.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import yaml

from frontdesk.world import CLINIC_FACTS, PROVIDERS, TODAY, VISIT_TYPES

GREETING = "Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?"


@dataclass
class Rule:
    id: str
    text: str
    locked: bool = False  # safety rules: the loop may add to them, never edit or remove them
    origin: dict = field(default_factory=dict)


@dataclass
class Policy:
    version: str
    persona: str
    rules: list[Rule]
    parent: str | None = None
    summary: str = ""
    path: Path | None = None

    @classmethod
    def load(cls, path: str | Path) -> "Policy":
        path = Path(path)
        d = yaml.safe_load(path.read_text(encoding="utf-8"))
        rules = [Rule(r["id"], r["text"].strip(), r.get("locked", False), r.get("origin", {})) for r in d["rules"]]
        return cls(d["version"], d["persona"].strip(), rules, d.get("parent"), d.get("summary", ""), path)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        d = {"version": self.version, "parent": self.parent, "summary": self.summary,
             "persona": self.persona,
             "rules": [{"id": r.id, "text": r.text, **({"locked": True} if r.locked else {}),
                        **({"origin": r.origin} if r.origin else {})} for r in self.rules]}
        path.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
        self.path = path
        return path

    def compile(self) -> str:
        """The system prompt the agent actually sees."""
        providers = "\n".join(
            f"- {p.name} (id {p.id}), {p.specialty}: {', '.join(p.visit_types)}. "
            f"{'Taking' if p.accepts_new_patients else 'Not taking'} new patients."
            for p in PROVIDERS)
        visit_types = "\n".join(f"- {k}: {v}" for k, v in VISIT_TYPES.items())
        rules = "\n".join(f"{i}. {r.text}" for i, r in enumerate(self.rules, 1))
        return (f"{self.persona}\n\n"
                f"The call has already started. You greeted the caller with: \"{GREETING}\"\n\n"
                f"CLINIC\n{CLINIC_FACTS}\n\nPROVIDERS\n{providers}\n\nVISIT TYPES\n{visit_types}\n\n"
                f"CALENDAR\n{calendar_block()}\n\nRULES\n{rules}\n")

    def child(self, version: str, summary: str) -> "Policy":
        return Policy(version, self.persona, copy.deepcopy(self.rules), self.version, summary)


def calendar_block() -> str:
    """Spell out the next three weeks. A small model doing date arithmetic in its head is
    a reliable source of 'Thursday the 23rd' errors; a lookup table is not."""
    monday = TODAY - timedelta(days=TODAY.weekday())
    lines = [f"Today is {TODAY:%A, %B} {TODAY.day}, {TODAY.year}, and it is 9:00 AM."]
    for label, start in [("This week", monday), ("Next week", monday + timedelta(7)),
                         ("The week after", monday + timedelta(14))]:
        days = ", ".join(f"{d:%a} {d:%b} {d.day} ({d.isoformat()})"
                         for d in (start + timedelta(i) for i in range(5)))
        lines.append(f"{label}: {days}")
    return "\n".join(lines)
