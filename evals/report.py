"""Markdown report for a loop run: scoreboard, per-scenario matrix, each patch and why it was kept or not."""
from __future__ import annotations

from pathlib import Path

from frontdesk.policy import Policy


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def one_line(version: str, s: dict) -> str:
    tr, ho, o = s["train"], s["holdout"], s["overall"]
    return (f"  {version}: train {tr['passed']}/{tr['n']} ({pct(tr['pass_rate'])}), holdout {ho['passed']}/{ho['n']} "
            f"({pct(ho['pass_rate'])}), mean score {o['mean_score']}, calls with a critical failure {o['critical_calls']}")


def scoreboard_rows(history: list[dict]) -> list[list[str]]:
    rows = []
    for h in history:
        s = h["summary"]
        rows.append([h["version"], h["status"], f"{s['train']['passed']}/{s['train']['n']} ({pct(s['train']['pass_rate'])})",
                     f"{s['holdout']['passed']}/{s['holdout']['n']} ({pct(s['holdout']['pass_rate'])})",
                     f"{s['overall']['mean_score']}", f"{s['overall']['critical_calls']}"])
    return rows


def scoreboard_text(history: list[dict]) -> str:
    head = ["version", "status", "train pass", "holdout pass", "mean score", "critical calls"]
    rows = [head] + scoreboard_rows(history)
    widths = [max(len(r[i]) for r in rows) for i in range(len(head))]
    return "\n".join("  " + "  ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows)


def _table(head: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(r) + " |" for r in rows])


def build(history: list[dict], out: Path, trials: int, llms: dict, improver) -> str:
    base = history[0]["summary"]
    md = [f"# Improvement loop report ({out.name})", "",
          f"Agent `{llms['agent'].model}` | caller simulator `{llms['caller'].model}` | judge `{llms['judge'].model}` "
          f"| improver `{improver.model}`. {len(base['by_scenario'])} scenarios x {trials} trials per version. "
          "A call passes with no critical and no major failure.", "",
          "## Scoreboard", "",
          _table(["version", "status", "train pass", "holdout pass", "mean score", "calls with a critical failure"],
                 scoreboard_rows(history)), ""]

    versions = [h for h in history]
    head = ["scenario", "split"] + [h["version"] for h in versions]
    rows = []
    for sid, b in base["by_scenario"].items():
        cells = []
        for h in versions:
            s = h["summary"]["by_scenario"].get(sid)
            cells.append("".join("P" if p else "." for p in s["trials"]) if s else "")
        rows.append([sid, b["split"]] + cells)
    rows.sort(key=lambda r: (r[1] != "train", r[0]))
    md += ["## Every call, by scenario", "", "`P` = passed, `.` = failed, one character per trial.", "",
           _table(head, rows), ""]

    md += ["## What the eval found in the baseline", "",
           _table(["check", "failed calls"], [[f"`{k}`", str(v)] for k, v in base["overall"]["failed_checks"].items()]), ""]

    for h in history[1:]:
        p, g = h["proposal"], h["gate"]
        md += [f"## {h['version']} (from {h['parent']}): {h['status'].upper()}", "",
               f"**Improver's diagnosis.** {p.get('diagnosis', '')}", "", "**Patch:**", ""]
        for op in p["ops"]:
            target = f" `{op['rule_id']}`" if op.get("rule_id") else ""
            md += [f"- `{op['op']}`{target}: \"{op.get('text', '')}\"",
                   f"  - fixes: {', '.join(op.get('fixes', []))}; why: {op.get('rationale', '')}; risk: {op.get('risk', '')}"]
        if p.get("suspected_eval_errors"):
            md += ["", "**Flagged by the improver as possible eval errors (not patched, for a human to review):**", ""]
            md += [f"- {e.get('scenario')} / `{e.get('check')}`: {e.get('why')}" for e in p["suspected_eval_errors"]]
        md += ["", f"**Gate:** {' '.join(g['reasons'])}"]
        if g["suspects"]:
            md += [f"Suspects re-run with {trials} extra trials: {', '.join(g['suspects'])}."]
        if g["improved"]:
            md += [f"Improved: {', '.join(g['improved'])}."]
        md += [""]

    final = next(h for h in reversed(history) if h["status"] in ("accepted", "baseline"))
    pol = Policy.load(out / "policies" / f"{final['version']}.yaml")
    md += [f"## Final policy ({final['version']})", ""]
    for r in pol.rules:
        src = r.origin.get("source", "")
        tag = " (locked)" if r.locked else ""
        verb = "rewritten" if "previous_text" in r.origin else "added"
        prov = "" if src == "baseline" else f" _({verb} in {r.origin.get('version')} for {', '.join(r.origin.get('fixes', []))})_"
        md.append(f"- **{r.id}**{tag}: {r.text}{prov}")
    md += [""]

    md += ["## Cost and latency", ""]
    rows = []
    for h in history:
        u, s = h["summary"].get("usage", {}), h["summary"]
        rows.append([h["version"], f"${u.get('total_usd', 0)}", f"{s['agent_turn_latency_s']['p50']}s",
                     f"{s['agent_turn_latency_s']['p95']}s", str(s["llm_calls_per_turn"])])
    md += [_table(["version", "eval cost (list price)", "agent turn p50", "agent turn p95", "model calls per turn"], rows), "",
           "Latency is model time only (no speech-to-text or text-to-speech), on Bedrock from India.", ""]
    return "\n".join(md)


def main() -> None:
    """Rebuild REPORT.md for a recorded run from its history.json (no model calls)."""
    import argparse
    import json
    from types import SimpleNamespace

    from frontdesk import config

    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--trials", type=int, default=None)
    args = ap.parse_args()
    history = json.loads((args.run / "history.json").read_text(encoding="utf-8"))
    trials = args.trials or json.loads((args.run / "args.json").read_text(encoding="utf-8"))["trials"]
    names = {r: SimpleNamespace(model=config.model_for(r)) for r in ("agent", "patient", "judge", "improver")}
    llms = {"agent": names["agent"], "caller": names["patient"], "judge": names["judge"]}
    (args.run / "REPORT.md").write_text(build(history, args.run, trials, llms, names["improver"]), encoding="utf-8")
    print(f"wrote {args.run / 'REPORT.md'}")


if __name__ == "__main__":
    main()
