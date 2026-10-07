"""Turn failed calls into one small, typed change to the policy book.

The improver is an LLM, but it is boxed in:
  - it only sees failures from the train split (the holdout split exists to catch overfitting),
  - it can only add, edit or remove rules (at most 3 operations), never rewrite the prompt,
  - it cannot touch locked safety rules,
  - code lints every proposal: a rule that names a patient, a date or an appointment id is a
    rule written for one test, and it is rejected before it costs an eval run,
  - it is told it may blame the eval instead of the agent, and those claims go to a human.
Whether the patch is kept is not its call. The gate decides, on a full re-run.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from frontdesk.config import SCENARIOS_DIR
from frontdesk.llm import LLM, parse_json_reply
from frontdesk.policy import Policy, Rule
from frontdesk.tools import TOOL_SPECS
from frontdesk.world import PATIENTS

MAX_OPS = 3
MAX_RULE_WORDS = 60
MAX_RULES = 15
SEVERITY_RANK = {"critical": 0, "major": 1, "minor": 2}

IMPROVER_SYSTEM = """You maintain the policy book for "Ava", an AI phone receptionist at a family clinic. The policy
book is a short numbered list of rules inside her system prompt. An evaluation ran Ava on simulated phone calls
and found the failures below. Propose ONE small patch to the rules that fixes the root cause of as many failures
as possible without breaking calls that already work.

Constraints:
- At most 3 operations. Each is add_rule, edit_rule or remove_rule.
- Rules marked LOCKED are safety rules. Do not edit or remove them (you may add a rule next to them).
- Write general behaviour that is right on every call. Never mention specific patients, names, dates,
  appointment ids or test scenarios: a rule that fits one test is overfitting and is rejected automatically.
- Each rule is one or two plain sentences, under 60 words, written as an instruction to Ava.
- Prefer one rule that fixes a shared root cause over several narrow ones. Prefer editing an existing rule to
  adding a near-duplicate. Everything Ava says is spoken by text-to-speech on a phone call.
- Think about side effects: a rule that fixes one failure can cause over-refusal, longer calls or new failures
  elsewhere. Name the main risk.
- Some failures may be evaluation errors (the simulated caller or the check got it wrong, not Ava). Do not
  patch for those. List them under suspected_eval_errors.

Return JSON only:
{"diagnosis": "2 to 4 sentences on what is going wrong and why",
 "ops": [{"op": "add_rule", "rule_id": "only for edit/remove", "text": "...", "fixes": ["check ids"],
          "rationale": "...", "risk": "..."}],
 "suspected_eval_errors": [{"scenario": "...", "check": "...", "why": "..."}]}"""


# ---- failures ------------------------------------------------------------------------------

def excerpt(rec: dict, turn: int | None, before: int = 4) -> str:
    turns = rec["turns"]
    end = len(turns) if turn is None else min(len(turns), turn + 2)
    start = max(0, (end - 6) if turn is None else turn - before)
    lines = []
    for t in turns[start:end]:
        if t["role"] == "caller":
            lines.append(f"CALLER: {t['heard']}")
            continue
        for e in t["events"]:
            res = json.dumps(e["result"])
            lines.append(f"  [tool] {e['name']}({json.dumps(e['input'])}) -> {res[:220]}{'...' if len(res) > 220 else ''}")
        lines.append(f"AVA: {t['heard']}" + ("  [caller talked over this]" if t.get("interrupted") else ""))
    return "\n".join(lines)


def collect_failures(records: list[dict], split: str = "train") -> list[dict]:
    out = []
    for r in records:
        if r["split"] != split:
            continue
        for c in r["checks"]:
            if not c["passed"]:
                out.append({"scenario": r["scenario"], "trial": r["trial"], "check": c["id"],
                            "severity": c["severity"], "detail": c["detail"], "turn": c.get("turn"),
                            "excerpt": excerpt(r, c.get("turn"))})
    return out


def group_failures(failures: list[dict]) -> list[dict]:
    groups: dict[str, list] = defaultdict(list)
    for f in failures:
        groups[f["check"]].append(f)
    out = []
    for check, fs in groups.items():
        seen, examples = set(), []
        for f in sorted(fs, key=lambda f: (f["scenario"], f["trial"])):
            if f["scenario"] not in seen and len(examples) < 2:
                seen.add(f["scenario"])
                examples.append(f)
        out.append({"check": check, "severity": fs[0]["severity"], "count": len(fs),
                    "scenarios": sorted({f["scenario"] for f in fs}), "examples": examples})
    return sorted(out, key=lambda g: (SEVERITY_RANK[g["severity"]], -g["count"], g["check"]))


def render_request(policy: Policy, groups: list[dict], passing_titles: list[str], rejected: list[dict]) -> str:
    rules = "\n".join(f"{r.id}{' [LOCKED]' if r.locked else ''}: {r.text}" for r in policy.rules)
    tools = "\n".join(f"- {t['name']}: {t['description']}" for t in TOOL_SPECS)
    parts = [f"CURRENT RULES\n{rules}", f"AVA'S TOOLS (fixed)\n{tools}",
             "CALLS THAT CURRENTLY PASS (keep them working)\n" + "\n".join(f"- {t}" for t in passing_titles)]
    fl = []
    for g in groups:
        fl.append(f"## {g['check']} ({g['severity']}): {g['count']} failure(s) in {', '.join(g['scenarios'])}")
        for ex in g["examples"]:
            fl.append(f"Example ({ex['scenario']}, trial {ex['trial']}): {ex['detail']}\n{ex['excerpt']}\n")
    parts.append("FAILURES (train split)\n" + "\n".join(fl))
    if rejected:
        rj = "\n".join(f"- ops: {json.dumps(r['ops'])}\n  rejected because: {'; '.join(r['reasons'])}" for r in rejected)
        parts.append(f"EARLIER PATCHES THAT THE GATE REJECTED (do not repeat them)\n{rj}")
    return "\n\n".join(parts)


# ---- lint ----------------------------------------------------------------------------------

_NAMES = sorted({w for p in PATIENTS for w in (p.first_name, p.last_name)}, key=len, reverse=True)
FORBIDDEN = [
    (re.compile(r"\b(" + "|".join(_NAMES) + r")\b"), "names a patient"),
    (re.compile(r"\b(A-\d{4}|PT-\d{4}|S-[A-Z]{3}-\d{4}-\d{4})\b"), "contains an internal id"),
    (re.compile(r"\b20\d\d-\d\d-\d\d\b|\b(January|February|March|April|May|June|July|August|September|October|"
                r"November|December)\s+\d{1,2}\b"), "contains a specific date"),
    (re.compile(r"\b(" + "|".join(sorted((p.stem for p in SCENARIOS_DIR.glob("*.yaml")), key=len, reverse=True))
                + r")\b"), "names a test scenario"),
]


def lint(ops: list[dict], policy: Policy) -> list[str]:
    errors = []
    if not ops:
        return ["the patch has no operations"]
    if len(ops) > MAX_OPS:
        errors.append(f"{len(ops)} operations; the limit is {MAX_OPS}")
    rules = {r.id: r for r in policy.rules}
    count = len(rules)
    for op in ops:
        kind = op.get("op")
        if kind not in ("add_rule", "edit_rule", "remove_rule"):
            errors.append(f"unknown op {kind!r}")
            continue
        if kind in ("edit_rule", "remove_rule"):
            rule = rules.get(op.get("rule_id", ""))
            if rule is None:
                errors.append(f"{kind}: no rule {op.get('rule_id')!r}")
                continue
            if rule.locked:
                errors.append(f"{kind}: {rule.id} is a locked safety rule")
        if kind in ("add_rule", "edit_rule"):
            text = (op.get("text") or "").strip()
            if not text:
                errors.append(f"{kind}: empty text")
            if len(text.split()) > MAX_RULE_WORDS:
                errors.append(f"{kind}: {len(text.split())} words; the limit is {MAX_RULE_WORDS}")
            for rx, why in FORBIDDEN:
                m = rx.search(text)
                if m:
                    errors.append(f"{kind}: rule {why} ('{m.group(0)}'), which is overfitting to a test")
        count += {"add_rule": 1, "remove_rule": -1}.get(kind, 0)
    if count > MAX_RULES:
        errors.append(f"the policy would have {count} rules; the limit is {MAX_RULES} (prompt length is latency on a call)")
    return errors


# ---- propose and apply ---------------------------------------------------------------------

def propose(policy: Policy, records: list[dict], passing_titles: list[str], rejected: list[dict], llm: LLM,
            scope: str, log=print) -> dict:
    groups = group_failures(collect_failures(records, "train"))
    request = render_request(policy, groups, passing_titles, rejected)
    messages = [{"role": "user", "content": [{"text": request}]}]
    for attempt in range(1, 4):
        reply = llm.chat(IMPROVER_SYSTEM, messages, scope=f"{scope}/a{attempt}")
        try:
            proposal = parse_json_reply(reply.text)
        except ValueError as e:
            errors = [f"reply was not valid JSON ({e})"]
            proposal = {}
        else:
            errors = lint(proposal.get("ops", []), policy)
        if not errors:
            proposal["lint_retries"] = attempt - 1
            proposal["failure_groups"] = [{k: g[k] for k in ("check", "severity", "count", "scenarios")} for g in groups]
            return proposal
        log(f"  lint rejected the proposal: {'; '.join(errors)}")
        messages += [{"role": "assistant", "content": [{"text": reply.text or "{}"}]},
                     {"role": "user", "content": [{"text": "That patch was rejected by the lint:\n- " + "\n- ".join(errors)
                                                   + "\nFix it and return the full JSON again."}]}]
    raise RuntimeError("improver could not produce a valid patch in 3 attempts")


def apply_patch(policy: Policy, proposal: dict, version: str, failures: list[dict]) -> Policy:
    new = policy.child(version, proposal.get("diagnosis", ""))
    by_id = {r.id: r for r in new.rules}
    next_num = max(int(r.id[1:]) for r in new.rules) + 1
    for op in proposal["ops"]:
        fixes = op.get("fixes", [])
        evidence = sorted({f"{f['scenario']}/t{f['trial']}" for f in failures if f["check"] in fixes})[:6]
        origin = {"source": "eval", "version": version, "fixes": fixes, "rationale": op.get("rationale", ""),
                  "risk": op.get("risk", ""), "evidence": evidence}
        if op["op"] == "add_rule":
            rule = Rule(f"R{next_num}", op["text"].strip(), False, origin)
            next_num += 1
            new.rules.append(rule)
            by_id[rule.id] = rule
        elif op["op"] == "edit_rule":
            rule = by_id[op["rule_id"]]
            rule.origin = {**origin, "previous_text": rule.text, "first_source": rule.origin.get("source")}
            rule.text = op["text"].strip()
        elif op["op"] == "remove_rule":
            new.rules = [r for r in new.rules if r.id != op["rule_id"]]
    return new
