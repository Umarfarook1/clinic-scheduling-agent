"""Keep a patch only if it helps and does not break anything.

With 3 trials per scenario one flaky call can look like a regression, and one lucky call can
look like a fix. So the gate works in two steps:
  1. Any scenario that got worse (fewer passes, or more calls with a critical failure) is a
     suspect. Suspects are re-run with extra trials before anyone believes them.
  2. A suspect is a confirmed regression if, over all its trials, its pass rate is still at
     least 0.25 lower, or its critical-failure rate at least 0.25 higher, than before.
A patch is accepted when the train split passes more calls than before and nothing regressed,
on either split. This catches breakages; 18 scenarios cannot detect a 5% improvement, and
the report says so instead of pretending.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

REGRESSION_MARGIN = 0.25


@dataclass
class GateResult:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    suspects: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)
    improved: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return asdict(self)


def _crit_rate(s: dict) -> float:
    return s["critical_calls"] / s["n"] if s["n"] else 0.0


def find_suspects(before: dict, after: dict) -> tuple[list[str], list[str]]:
    suspects, improved = [], []
    for sid, b in before["by_scenario"].items():
        a = after["by_scenario"].get(sid)
        if a is None:
            continue
        if a["passed"] < b["passed"] or a["critical_calls"] > b["critical_calls"]:
            suspects.append(sid)
        elif a["passed"] > b["passed"]:
            improved.append(sid)
    return suspects, improved


def decide(before: dict, after: dict, confirmed: dict) -> GateResult:
    """before/after: summaries over the same number of trials. confirmed: summary of the
    candidate over the original plus the extra trials, for suspect scenarios only."""
    suspects, improved = find_suspects(before, after)
    regressions = []
    for sid in suspects:
        b = before["by_scenario"][sid]
        a = confirmed["by_scenario"].get(sid, after["by_scenario"][sid])
        if (b["pass_rate"] - a["pass_rate"] >= REGRESSION_MARGIN
                or _crit_rate(a) - _crit_rate(b) >= REGRESSION_MARGIN):
            regressions.append(f"{sid} ({b['split']}): {b['passed']}/{b['n']} -> {a['passed']}/{a['n']} passing, "
                               f"critical calls {b['critical_calls']} -> {a['critical_calls']}")
    reasons = []
    tb, ta = before["train"]["passed"], after["train"]["passed"]
    if ta <= tb:
        reasons.append(f"train did not improve ({tb} -> {ta} passing calls)")
    if regressions:
        reasons.append(f"{len(regressions)} confirmed regression(s): " + "; ".join(regressions))
    cleared = [s for s in suspects if not any(r.startswith(s + " ") for r in regressions)]
    return GateResult(accepted=not reasons, reasons=reasons or [f"train {tb} -> {ta} passing calls, no regressions"
                                                                + (f" ({len(cleared)} suspect(s) cleared on re-run)" if cleared else "")],
                      suspects=suspects, regressions=regressions, improved=improved)
