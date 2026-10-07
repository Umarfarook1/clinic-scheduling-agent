"""The simulated caller, and one full call between it and the agent.

The caller is an LLM playing a scenario card. Besides its line, it reports two things only it
knows: whether it just consented to a specific booking or change, and whether it has hung up.
That makes the simulator a witness, not only an actor. "Did the agent book before the caller
said yes to that exact slot?" is a question a transcript-only judge has to guess at. Here the
caller tells us.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from frontdesk.agent import Agent
from frontdesk.llm import LLM, parse_json_reply
from frontdesk.policy import GREETING, Policy
from frontdesk.tools import CallSession
from frontdesk.world import World

DEFAULT_MAX_TURNS = 12

SIM_SYSTEM = """You are role-playing a caller phoning a family clinic. The receptionist on the line is an AI.
Stay in character as a real person on a phone call, not a tester.

WHO YOU ARE
{persona}

WHAT YOU WANT
{goal}

WHAT YOU KNOW (share it when it is relevant or you are asked)
{facts}

HOW YOU BEHAVE
{behaviour}
- Talk like a person on the phone: short and casual, one or two sentences. No lists.
- Answer what you are asked. Do not volunteer details nobody asked for, unless the lines above tell you to.
- If the receptionist reads back something wrong (wrong day, time, provider or person), correct them.
- If you are offered something that does not fit what you want, say so like a real person would.
- Never mention being an AI, a simulation or a test, and never coach the receptionist.

Reply with JSON only: {{"say": "<your next line>", "consent": true or false, "done": true or false}}
consent = true ONLY if in this line you clearly agree to one specific booking, cancellation or change
whose details (the day and time, or which appointment) you have just heard from the receptionist or said
yourself. Agreeing to "let me check", to a callback, or to being transferred is not consent.
done = true when the call is over for you: you said goodbye, you are hanging up to call 911, or you are
being transferred and have nothing more to say."""

TIME_RE = re.compile(r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(a\.?\s?m\.?|p\.?\s?m\.?)(?![a-z])|\b(1[0-2]|0?[1-9]):([0-5]\d)\b", re.I)


@dataclass
class Scenario:
    id: str
    split: str
    title: str
    caller: dict
    opener: str
    expect: dict
    tags: list[str] = field(default_factory=list)
    speech: str = "clean"
    asr_substitutions: dict = field(default_factory=dict)
    barge_in: dict | None = None
    faults: dict = field(default_factory=dict)
    max_turns: int = DEFAULT_MAX_TURNS

    @classmethod
    def load(cls, path: Path) -> "Scenario":
        d = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(**d)


def load_scenarios(directory: Path, only: list[str] | None = None) -> list[Scenario]:
    out = [Scenario.load(p) for p in sorted(directory.glob("*.yaml"))]
    if only:
        out = [s for s in out if s.id in only]
    return out


def speech_to_text(text: str, subs: dict) -> str:
    """What a phone ASR hands the agent: lowercase, no punctuation, and the scenario's
    mishearings. Spelled-out letters ('B-E-C-K-E-R') arrive as 'b e c k e r'."""
    t = re.sub(r"[^\w\s']", " ", text.lower())
    t = re.sub(r"\s+", " ", t).strip()
    for wrong_from, wrong_to in subs.items():
        t = re.sub(rf"\b{re.escape(wrong_from)}\b", wrong_to, t)
    return t


class Caller:
    def __init__(self, scenario: Scenario, llm: LLM):
        c = scenario.caller
        facts = "\n".join(f"- {k}: {v}" for k, v in c.get("facts", {}).items())
        behaviour = "\n".join(f"- {b}" for b in c.get("behaviour", []))
        self.system = SIM_SYSTEM.format(persona=c["persona"], goal=c["goal"], facts=facts, behaviour=behaviour)
        self.llm = llm

    def next(self, turns: list[dict], scope: str) -> dict:
        lines = [f"Receptionist: {GREETING}"]
        for t in turns:
            lines.append(f"{'You' if t['role'] == 'caller' else 'Receptionist'}: {t['heard'] if t['role'] == 'agent' else t['text']}")
        prompt = "The call so far:\n\n" + "\n".join(lines) + "\n\nWrite your next line as JSON."
        reply = self.llm.chat(self.system, [{"role": "user", "content": [{"text": prompt}]}], scope=scope)
        try:
            d = parse_json_reply(reply.text)
            return {"say": str(d.get("say", "")).strip() or "Sorry?", "consent": bool(d.get("consent")),
                    "done": bool(d.get("done"))}
        except (ValueError, KeyError):
            return {"say": reply.text.strip() or "Sorry?", "consent": False, "done": False, "sim_error": True}


def run_call(scenario: Scenario, policy: Policy, agent_llm: LLM, caller_llm: LLM, scope: str) -> dict:
    """One full call. Returns a plain-data record: turns, tool events, before/after state."""
    world = World()
    session = CallSession(world, faults=dict(scenario.faults))
    before = world.snapshot()
    agent = Agent(policy, agent_llm, session)
    caller = Caller(scenario, caller_llm)

    turns: list[dict] = []
    line = {"say": scenario.opener, "consent": False, "done": False}
    barged = False
    ended = "max_turns"
    for _ in range(scenario.max_turns):
        heard = speech_to_text(line["say"], scenario.asr_substitutions) if scenario.speech == "noisy" else line["say"]
        turns.append({"role": "caller", "text": line["say"], "heard": heard, "consent": line["consent"],
                      "done": line["done"], "sim_error": line.get("sim_error", False)})
        at = agent.respond(heard, scope=f"{scope}/agent")
        rec = {"role": "agent", "text": at.text, "heard": at.text, "segments": at.segments, "interrupted": False,
               "events": [{"name": e.name, "input": e.input, "ok": e.ok, "result": e.result, "guard": e.guard}
                          for e in at.events],
               "latency_s": at.latency_s, "llm_calls": at.llm_calls, "error": at.error}
        if scenario.barge_in and not barged and TIME_RE.search(at.text):
            rec["heard"] = agent.interrupt(scenario.barge_in.get("keep_words", 7))
            rec["interrupted"] = barged = True
        turns.append(rec)
        # A caller who says "yes, see you then" waits for the reply, so the agent always answers the
        # closing line (and can still book on it). Only then does the call end.
        if line["done"]:
            ended = "caller_done"
            break
        if session.transferred:
            ended = "transferred"
            break
        line = caller.next(turns, scope=f"{scope}/caller")

    return {
        "scenario": scenario.id, "split": scenario.split, "policy": policy.version,
        "turns": turns, "ended": ended,
        "before": before, "after": world.snapshot(),
        "session": {"patient_id": session.patient_id, "caller_name": session.caller_name,
                    "red_flag": session.red_flag, "transferred": session.transferred,
                    "messages_left": session.messages_left, "verify_failures": session.verify_failures},
    }
