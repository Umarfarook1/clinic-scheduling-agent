"""The improvement loop: evaluate, turn failures into a patch, re-run everything, gate, repeat.

    python -m evals.loop                          # live, from policies/v0.yaml, records a cassette
    python -m evals.loop --replay runs/<run-id>   # re-run a recorded loop offline, no API key

Every round re-runs the FULL suite (train and holdout), not only the scenarios that failed,
because the interesting question is never "did the fix fix it", it is "what else moved".
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from evals import report
from evals.gate import decide, find_suspects
from evals.improve import apply_patch, collect_failures, propose
from evals.run import evaluate, make_llms, meter_snapshot, summarize, usage_between
from evals.simulate import load_scenarios
from frontdesk import config
from frontdesk.llm import LLM, Cassette
from frontdesk.policy import Policy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=Path, default=config.POLICIES_DIR / "v0.yaml")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--replay", type=Path, default=None, help="a recorded run directory to replay offline")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--only", default="", help="comma-separated scenario ids (for quick dev runs)")
    ap.add_argument("--pace", type=float, default=0.0, help="seconds to pause per log line (makes a replay watchable)")
    args = ap.parse_args()

    if args.replay:
        saved = json.loads((args.replay / "args.json").read_text(encoding="utf-8"))
        args.rounds, args.trials, args.only = saved["rounds"], saved["trials"], saved.get("only", "")
        args.start = args.replay / "policies" / "v0.yaml"
        out = args.out or args.replay.with_name(args.replay.name + "-replay")
        if out.exists():
            shutil.rmtree(out)
        cassette = Cassette(args.replay / "cassette.jsonl", "replay")
    else:
        out = args.out or config.RUNS_DIR / time.strftime("%Y%m%d-%H%M")
        cassette = Cassette(out / "cassette.jsonl", "record")
    out.mkdir(parents=True, exist_ok=True)
    (out / "args.json").write_text(json.dumps({"rounds": args.rounds, "trials": args.trials, "only": args.only}), encoding="utf-8")

    logf = (out / "loop.log").open("w", encoding="utf-8")

    def log(msg: str = "") -> None:
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()
        if args.pace:
            time.sleep(args.pace * (8 if msg.startswith(("==", "  GATE", "  diagnosis")) else 1))

    llms = make_llms(cassette)
    improver = LLM("improver", temperature=None, max_tokens=4000, cassette=cassette)
    scenarios = load_scenarios(config.SCENARIOS_DIR, [s for s in args.only.split(",") if s] or None)
    titles = {s.id: s.title for s in scenarios}
    k = args.trials

    current = Policy.load(args.start)
    current.save(out / "policies" / f"{current.version}.yaml")
    log(f"== Evaluating {current.version}: {len(scenarios)} scenarios x {k} trials "
        f"(agent {llms['agent'].model}, caller {llms['caller'].model}, judge {llms['judge'].model})")
    m0 = meter_snapshot(llms)
    cur_records = evaluate(current, scenarios, k, llms, out / current.version, args.workers, log=log)
    cur_sum = summarize(cur_records)
    cur_sum["usage"] = usage_between(m0, meter_snapshot(llms))
    log(report.one_line(current.version, cur_sum))

    history = [{"version": current.version, "parent": None, "status": "baseline", "summary": cur_sum}]
    rejected: list[dict] = []
    n = int(current.version[1:]) + 1
    for rnd in range(1, args.rounds + 1):
        failures = collect_failures(cur_records, "train")
        if not any(f["severity"] != "minor" for f in failures):
            log(f"\n== No critical or major failures left on train after {current.version}; stopping.")
            break
        version = f"v{n}"
        n += 1
        log(f"\n== Round {rnd}: {len(failures)} failing checks on train. Asking the improver for a patch -> {version}")
        passing = [titles[sid] for sid, s in cur_sum["by_scenario"].items()
                   if s["split"] == "train" and s["passed"] == s["n"]]
        proposal = propose(current, cur_records, passing, rejected, improver, scope=f"improve/{version}", log=log)
        log(f"  diagnosis: {proposal.get('diagnosis', '')}")
        for op in proposal["ops"]:
            log(f"  {op['op']} {op.get('rule_id', '')}: {op.get('text', '')}")
        for e in proposal.get("suspected_eval_errors", []):
            log(f"  (improver thinks this is an eval error, not patched: {e.get('scenario')} / {e.get('check')}: {e.get('why')})")
        candidate = apply_patch(current, proposal, version, failures)
        candidate.save(out / "policies" / f"{version}.yaml")

        log(f"== Re-running the full suite on {version}")
        m0 = meter_snapshot(llms)
        cand_records = evaluate(candidate, scenarios, k, llms, out / version, args.workers, log=log)
        cand_sum = summarize(cand_records)
        suspects, _ = find_suspects(cur_sum, cand_sum)
        confirmed_sum = cand_sum
        if suspects:
            log(f"  {len(suspects)} scenario(s) look worse: {', '.join(suspects)}. Re-running them {k} more times before believing it.")
            extra = evaluate(candidate, [s for s in scenarios if s.id in suspects], k, llms,
                             out / f"{version}-confirm", args.workers, trial_start=k + 1, log=log)
            confirmed_sum = summarize(cand_records + extra)
        cand_sum["usage"] = usage_between(m0, meter_snapshot(llms))
        gate = decide(cur_sum, cand_sum, confirmed_sum)
        log(report.one_line(version, cand_sum))
        log(f"  GATE: {'ACCEPTED' if gate.accepted else 'REJECTED'}. {' '.join(gate.reasons)}")
        history.append({"version": version, "parent": current.version, "status": "accepted" if gate.accepted else "rejected",
                        "summary": cand_sum, "confirmed": confirmed_sum if suspects else None,
                        "proposal": proposal, "gate": gate.to_json()})
        if gate.accepted:
            current, cur_records, cur_sum, rejected = candidate, cand_records, cand_sum, []
        else:
            rejected.append({"ops": proposal["ops"], "reasons": gate.reasons})

    (out / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    md = report.build(history, out, k, llms, improver)
    (out / "REPORT.md").write_text(md, encoding="utf-8")
    log(f"\n== Final: {current.version}. Report: {out / 'REPORT.md'}")
    log(report.scoreboard_text(history))
    if not args.replay:
        for h in history:
            if h["status"] in ("baseline", "accepted"):
                src = out / "policies" / f"{h['version']}.yaml"
                dst = config.POLICIES_DIR / src.name
                if not dst.exists():
                    shutil.copy(src, dst)
    logf.close()


if __name__ == "__main__":
    main()
