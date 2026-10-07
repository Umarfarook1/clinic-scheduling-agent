"""How blind is a transcript-only judge, and how much do two different judges agree?

    python -m evals.blindspot runs/<run-id>/v0

1. Blind judge: one pass/fail per call from the words alone (no tools, no clinic state). Every
   call the full harness fails but the blind judge passes is a blind spot, broken down by
   which check caught it.
2. Second judge: a model from a different family (gpt-oss-120b on Bedrock by default) grades
   the same four rubric items as the main judge. Agreement per item says how much the judge
   verdicts can be trusted at all.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evals.judge import ITEMS, blind_verdict, judge_record
from evals.run import load_records
from frontdesk.llm import LLM, Cassette


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path, help="a version directory inside a run, e.g. runs/<id>/v0")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    records = load_records(args.results)
    cassette = Cassette(args.results.parent / "cassette.jsonl", "replay" if args.replay else "record")
    blind_llm = LLM("judge", temperature=0.0, max_tokens=300, cassette=cassette)
    judge2 = LLM("judge2", temperature=0.0, max_tokens=3000, cassette=cassette)

    def work(r):
        scope = f"{r['policy']}/{r['scenario']}/t{r['trial']}"
        return blind_verdict(r, blind_llm, f"blind/{scope}"), judge_record(r, judge2, f"judge2/{scope}")

    with ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(work, records))

    # 1. blind spots
    cells = Counter()
    missed_by_check: Counter = Counter()
    examples = []
    for r, (blind, _) in zip(records, results):
        cells[(r["passed"], blind["pass"])] += 1
        if not r["passed"] and blind["pass"]:
            serious = [c for c in r["checks"] if not c["passed"] and c["severity"] in ("critical", "major")]
            for c in serious:
                missed_by_check[c["id"]] += 1
            if serious and len(examples) < 6:
                examples.append((r, serious[0], blind["why"]))
    fails = sum(1 for r in records if not r["passed"])
    missed = cells[(False, True)]
    # Formatting failures (markdown, long turns) are easy to argue about, so also count only calls
    # that failed on the state, the trace, consent, privacy or safety.
    voice = {"speakable", "brief_turns", "options_per_turn", "no_question_before_tool"}
    substantive = [(r, b) for r, (b, _) in zip(records, results)
                   if any(not c["passed"] and c["severity"] in ("critical", "major") and c["id"] not in voice
                          for c in r["checks"])]
    sub_missed = sum(1 for _, b in substantive if b["pass"])

    # 2. judge agreement
    agree = Counter()
    total = Counter()
    disagreements = []
    for r, (_, j2) in zip(records, results):
        j1 = {c["id"]: c for c in r["checks"] if c["source"] == "judge"}
        for c2 in j2:
            c1 = j1.get(c2.id)
            if c1 is None or c2.id == "judge_error":
                continue
            total[c2.id] += 1
            if c1["passed"] == c2.passed:
                agree[c2.id] += 1
            elif len(disagreements) < 6:
                disagreements.append((r, c2.id, c1["passed"], c2.passed, c1["detail"] or c2.detail))

    md = [f"# What a transcript-only judge misses ({args.results})", "",
          f"{len(records)} calls. The full harness failed {fails}. A judge that only reads the transcript passed "
          f"**{missed} of those {fails}** ({missed / fails:.0%}) as fine." if fails else "No failures to compare.", "",
          "| | blind judge: pass | blind judge: fail |", "|---|---|---|",
          f"| harness: pass | {cells[(True, True)]} | {cells[(True, False)]} |",
          f"| harness: fail | **{cells[(False, True)]}** | {cells[(False, False)]} |", "",
          f"Most of those are formatting failures, which a lenient reader might forgive. Counting only calls that "
          f"failed on the clinic state, the tool trace, consent, privacy or safety: **{sub_missed} of "
          f"{len(substantive)}** passed the transcript-only judge.", "",
          "Failures the blind judge waved through, by the check that caught them:", "",
          "| check | calls |", "|---|---|"]
    md += [f"| `{k}` | {v} |" for k, v in missed_by_check.most_common()]
    md += ["", "Examples:", ""]
    for r, c, why in examples:
        md.append(f"- **{r['scenario']}** t{r['trial']}: harness `{c['id']}`: {c['detail']}  \n  blind judge: \"{why}\"")
    model2 = judge2.model
    md += ["", f"# Judge agreement: main judge vs `{model2}`", "",
           "| item | severity | agree | of |", "|---|---|---|---|"]
    md += [f"| `{k}` | {ITEMS[k.split(':', 1)[1]][0]} | {agree[k]} ({agree[k] / total[k]:.0%}) | {total[k]} |"
           for k in sorted(total)]
    md += ["", "Disagreements (first few):", ""]
    for r, item, p1, p2, detail in disagreements:
        md.append(f"- **{r['scenario']}** t{r['trial']} `{item}`: main judge {'pass' if p1 else 'FAIL'}, "
                  f"second judge {'pass' if p2 else 'FAIL'}. {detail}")
    out = args.results / "BLINDSPOT.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:12]))
    print(f"\nWritten to {out}")
    (args.results / "blindspot.json").write_text(json.dumps({
        "calls": len(records), "harness_failed": fails, "blind_passed_harness_failures": missed,
        "substantive_failures": len(substantive), "blind_passed_substantive": sub_missed,
        "missed_by_check": dict(missed_by_check),
        "judge_agreement": {k: [agree[k], total[k]] for k in total}}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
