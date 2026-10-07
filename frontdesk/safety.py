"""A deterministic red-flag screen that runs on every caller utterance before the LLM sees it.

This is defense in depth, not the safety system. Keyword lists always miss paraphrases ("his
words are coming out jumbled" is a stroke sign with no keyword in it), so the agent's own
judgment still has to catch those. What the screen buys is a hard floor: once it fires, the
booking tools refuse to book for the rest of the call, whatever the model decides.
"""
from __future__ import annotations

import re

RED_FLAGS = [
    r"chest (pain|pressure|tightness)",
    r"(can'?t|cannot|trouble|hard to) breath",
    r"short(ness)? of breath",
    r"suicid", r"kill (myself|himself|herself)", r"end (my|his|her) life", r"overdos",
    r"passed out", r"unconscious", r"seizure",
    r"(severe|heavy|won'?t stop) bleeding", r"bleeding (heavily|a lot)",
    r"face (droop|drooping)", r"slurred speech", r"stroke",
]
_PATTERN = re.compile("|".join(RED_FLAGS), re.IGNORECASE)


def screen(utterance: str) -> str | None:
    """Return the matched phrase if the utterance contains a red flag."""
    m = _PATTERN.search(utterance)
    return m.group(0) if m else None
