"""Run the scenario suite against one policy version and score it.

    python -m evals.run --policy policies/v0.yaml --trials 3
    python -m evals.run --policy policies/v0.yaml --only emergency_chest_pain,saturday_bait --trials 1

Each scenario runs several times because one LLM conversation is one sample, not a result.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from evals.checks import grade, run_code_checks, to_dicts
from evals.judge import judge_record
from evals.simulate import Scenario, load_scenarios, run_call
from frontdesk import config
from frontdesk.llm import LLM, Cassette
from frontdesk.policy import GREETING, Policy


def make_llms(cassette: Cassette) -> dict[str, LLM]:
    return {
        # A little temperature on both sides so repeated trials are real samples, not copies.
        "agent": LLM("agent", temperature=0.2, max_tokens=600, cassette=cassette),
        "caller": LLM("patient", temperature=0.7, max_tokens=300, cassette=cassette),
        "judge": LLM("judge", temperature=0.0, max_tokens=1500, cassette=cassette),
    }


def evaluate(policy: Policy, scenarios: list[Scenario], trials: int, llms: dict[str, LLM], out_dir: Path,
             workers: int = 6, judge: bool = True, trial_start: int = 1, log=print) -> list[dict]:
    by_id = {s.id: s for s in scenarios}
    jobs = [(s.id, t) for s in scenarios for t in range(trial_start, trial_start + trials)]

    def job(sid: str, trial: int) -> dict:
        s = by_id[sid]
        scope = f"{policy.version}/{sid}/t{trial}"
        rec = run_call(s, policy, llms["agent"], llms["caller"], scope)
        rec["trial"] = trial
        checks = run_code_checks(rec, s)
        if judge:
            checks += judge_record(rec, llms["judge"], scope=f"{scope}/judge")
        rec["checks"] = to_dicts(checks)
        rec["passed"], rec["score"] = grade(checks)
        return rec

    records: list[dict] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(job, sid, t): (sid, t) for sid, t in jobs}
        for f in as_completed(futures):
            sid, t = futures[f]
            try:
                rec = f.result()
            except Exception:
                log(f"  ! {sid} t{t} crashed, retrying once:\n{traceback.format_exc(limit=2)}")
                rec = job(sid, t)
            records.append(rec)
            failed = [c["id"] for c in rec["checks"] if not c["passed"] and c["severity"] != "minor"]
            log(f"  {'PASS' if rec['passed'] else 'FAIL'}  {policy.version}  {sid:<30} t{t}  "
                f"score {rec['score']:>3}  {', '.join(failed)}")
    records.sort(key=lambda r: (r["scenario"], r["trial"]))
    log(f"  {len(records)} calls in {time.time() - t0:.0f}s")
    save(records, out_dir)
    return records


# ---- summaries -----------------------------------------------------------------------------

def _stats(recs: list[dict]) -> dict:
    if not recs:
        return {"n": 0, "passed": 0, "pass_rate": 0.0, "mean_score": 0.0, "critical_calls": 0, "failed_checks": {}}
    failed = Counter(c["id"] for r in recs for c in r["checks"] if not c["passed"])
    return {
        "n": len(recs), "passed": sum(r["passed"] for r in recs),
        "pass_rate": round(sum(r["passed"] for r in recs) / len(recs), 3),
        "mean_score": round(statistics.mean(r["score"] for r in recs), 1),
        "critical_calls": sum(any(not c["passed"] and c["severity"] == "critical" for c in r["checks"]) for r in recs),
        "failed_checks": dict(failed.most_common()),
    }


def summarize(records: list[dict]) -> dict:
    by_s: dict[str, list] = defaultdict(list)
    for r in records:
        by_s[r["scenario"]].append(r)
    lat = [t["latency_s"] for r in records for t in r["turns"] if t["role"] == "agent"]
    calls = [t["llm_calls"] for r in records for t in r["turns"] if t["role"] == "agent"]
    q = statistics.quantiles(lat, n=20) if len(lat) >= 20 else [0] * 19
    return {
        "overall": _stats(records),
        "train": _stats([r for r in records if r["split"] == "train"]),
        "holdout": _stats([r for r in records if r["split"] == "holdout"]),
        "by_scenario": {sid: {"split": rs[0]["split"], **_stats(rs), "trials": [r["passed"] for r in rs]}
                        for sid, rs in sorted(by_s.items())},
        "agent_turn_latency_s": {"p50": round(statistics.median(lat), 2) if lat else 0, "p95": round(q[18], 2)},
        "llm_calls_per_turn": round(statistics.mean(calls), 2) if calls else 0,
    }


def meter_snapshot(llms: dict[str, LLM]) -> dict:
    return {k: (v.model, v.meter.calls, v.meter.input_tokens, v.meter.output_tokens) for k, v in llms.items()}


def usage_between(a: dict, b: dict) -> dict:
    out, total = {}, 0.0
    for role in b:
        model, c1, i1, o1 = b[role]
        _, c0, i0, o0 = a.get(role, (model, 0, 0, 0))
        pin, pout = config.price_for(model)
        cost = ((i1 - i0) * pin + (o1 - o0) * pout) / 1e6
        total += cost
        out[role] = {"model": model, "calls": c1 - c0, "input_tokens": i1 - i0, "output_tokens": o1 - o0,
                     "usd": round(cost, 3)}
    out["total_usd"] = round(total, 2)
    return out


# ---- files ---------------------------------------------------------------------------------

def save(records: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "results.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    tdir = out_dir / "transcripts"
    tdir.mkdir(exist_ok=True)
    for r in records:
        (tdir / f"{r['scenario']}__t{r['trial']}.md").write_text(transcript_md(r), encoding="utf-8")


def load_records(out_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (out_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if line]


def transcript_md(r: dict) -> str:
    from evals.checks import describe_diff
    lines = [f"# {r['scenario']} (trial {r['trial']}, policy {r['policy']}): "
             f"{'PASS' if r['passed'] else 'FAIL'}, score {r['score']}", "",
             f"**Ava:** {GREETING}", ""]
    for i, t in enumerate(r["turns"]):
        if t["role"] == "caller":
            heard = f"  \n_(speech-to-text heard: \"{t['heard']}\")_" if t["heard"] != t["text"] else ""
            flags = " `[consents]`" if t.get("consent") else ""
            lines += [f"**Caller [{i}]:** {t['text']}{flags}{heard}", ""]
            continue
        for e in t["events"]:
            tag = f" **BLOCKED ({e['guard']})**" if e["guard"] else ""
            lines.append(f"> `{e['name']}({json.dumps(e['input'], ensure_ascii=False)})`{tag}  ")
            lines.append(f"> `-> {json.dumps(e['result'], ensure_ascii=False)[:400]}`  ")
        if t["events"]:
            lines.append("")
        cut = f"  \n_(caller talked over this; heard only: \"{t['heard']}\")_" if t.get("interrupted") else ""
        lines += [f"**Ava [{i}]:** {t['text']}{cut}  _({t['latency_s']}s, {t['llm_calls']} model calls)_", ""]
    lines += [f"_Call ended: {r['ended']}. Clinic system change: {describe_diff(r)}._", "", "## Checks", ""]
    for c in sorted(r["checks"], key=lambda c: (c["passed"], c["severity"] != "critical", c["severity"] != "major")):
        mark = "pass" if c["passed"] else "**FAIL**"
        where = f" (turn {c['turn']})" if c.get("turn") is not None else ""
        lines.append(f"- {mark} [{c['severity']}, {c['source']}] `{c['id']}`{where} {c['detail']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", type=Path, default=config.POLICIES_DIR / "v0.yaml")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    policy = Policy.load(args.policy)
    scenarios = load_scenarios(config.SCENARIOS_DIR, [s for s in args.only.split(",") if s] or None)
    out = args.out or config.RUNS_DIR / f"{time.strftime('%Y%m%d-%H%M')}-{policy.version}"
    llms = make_llms(Cassette(out / "cassette.jsonl", "record"))
    m0 = meter_snapshot(llms)
    records = evaluate(policy, scenarios, args.trials, llms, out / policy.version, args.workers, not args.no_judge)
    summary = summarize(records)
    summary["usage"] = usage_between(m0, meter_snapshot(llms))
    (out / policy.version / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    o = summary["overall"]
    print(f"\n{policy.version}: {o['passed']}/{o['n']} calls passed ({o['pass_rate']:.0%}), mean score "
          f"{o['mean_score']}, {o['critical_calls']} calls with a critical failure. "
          f"Cost ~${summary['usage']['total_usd']}. Results in {out}")


if __name__ == "__main__":
    main()
