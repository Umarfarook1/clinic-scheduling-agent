"""Lint, patch application, the gate, the cassette, and the agent loop with a fake model."""
import json

from evals.gate import decide
from evals.improve import apply_patch, lint
from frontdesk.agent import Agent
from frontdesk.llm import LLM, Cassette, CassetteMiss, Reply, parse_json_reply, to_openai_messages
from frontdesk.policy import Policy
from frontdesk.tools import CallSession
from frontdesk.world import World

V0 = Policy.load("policies/v0.yaml")


# ---- lint and patches ----------------------------------------------------------------------

def test_lint_rejects_overfitting_and_locked_edits():
    errs = lint([{"op": "add_rule", "text": "If Maria calls about A-2001 on October 15, say no."},
                 {"op": "edit_rule", "rule_id": "R4", "text": "x"},
                 {"op": "add_rule", "text": "When saturday_bait happens, refuse."}], V0)
    joined = " ".join(errs)
    assert "patient" in joined and "id" in joined and "date" in joined and "locked" in joined and "scenario" in joined


def test_lint_allows_general_rules_that_name_tools():
    assert lint([{"op": "add_rule", "text": "After telling a caller to call 911, call transfer_to_staff with urgency emergency."}], V0) == []


def test_lint_limits_size():
    assert lint([{"op": "add_rule", "text": "word " * 61}], V0)
    assert lint([{"op": "add_rule", "text": "a"}] * 4, V0)


def test_apply_patch_keeps_provenance():
    proposal = {"diagnosis": "d", "ops": [
        {"op": "add_rule", "text": "Never use lists.", "fixes": ["speakable"], "rationale": "tts", "risk": "none"},
        {"op": "edit_rule", "rule_id": "R5", "text": "Keep replies under two sentences.", "fixes": ["brief_turns"]}]}
    failures = [{"scenario": "s1", "trial": 1, "check": "speakable"}]
    new = apply_patch(V0, proposal, "v1", failures)
    added = new.rules[-1]
    assert added.id == "R6" and added.origin["evidence"] == ["s1/t1"] and new.parent == "v0"
    assert next(r for r in new.rules if r.id == "R5").origin["previous_text"].startswith("Keep your replies")
    assert len(V0.rules) == 5  # the parent is untouched


# ---- gate ----------------------------------------------------------------------------------

def summary(train_passed, scen):
    by = {sid: {"split": split, "passed": p, "n": n, "pass_rate": p / n, "critical_calls": c}
          for sid, (split, p, n, c) in scen.items()}
    return {"train": {"passed": train_passed}, "by_scenario": by}


def test_gate_accepts_improvement_without_regression():
    before = summary(3, {"a": ("train", 0, 3, 0), "b": ("holdout", 3, 3, 0)})
    after = summary(6, {"a": ("train", 3, 3, 0), "b": ("holdout", 3, 3, 0)})
    assert decide(before, after, after).accepted


def test_gate_rejects_a_confirmed_holdout_regression():
    before = summary(3, {"a": ("train", 0, 3, 0), "b": ("holdout", 3, 3, 0)})
    after = summary(6, {"a": ("train", 3, 3, 0), "b": ("holdout", 1, 3, 0)})
    confirmed = summary(6, {"a": ("train", 3, 3, 0), "b": ("holdout", 3, 6, 0)})
    g = decide(before, after, confirmed)
    assert not g.accepted and g.regressions and "b" in g.suspects


def test_gate_clears_a_one_off_flake_on_rerun():
    before = summary(3, {"a": ("train", 0, 3, 0), "b": ("holdout", 3, 3, 0)})
    after = summary(6, {"a": ("train", 3, 3, 0), "b": ("holdout", 2, 3, 0)})
    confirmed = summary(6, {"a": ("train", 3, 3, 0), "b": ("holdout", 5, 6, 0)})
    assert decide(before, after, confirmed).accepted


def test_gate_rejects_no_train_gain():
    s = summary(3, {"a": ("train", 3, 3, 0)})
    assert not decide(s, s, s).accepted


# ---- llm plumbing --------------------------------------------------------------------------

class Scripted(LLM):
    def __init__(self, replies, **kw):
        super().__init__("agent", model="fake", **kw)
        self.replies = list(replies)

    def _call_with_retry(self, system, messages, tools):
        return self.replies.pop(0)


def test_cassette_replays_without_network(tmp_path):
    path = tmp_path / "c.jsonl"
    rec = Scripted([Reply([{"text": "hello"}], {"inputTokens": 5, "outputTokens": 1}, 0.5)],
                   cassette=Cassette(path, "record"))
    assert rec.chat("sys", [{"role": "user", "content": [{"text": "hi"}]}], scope="s").text == "hello"
    rep = Scripted([], cassette=Cassette(path, "replay"))
    assert rep.chat("sys", [{"role": "user", "content": [{"text": "hi"}]}], scope="s").text == "hello"
    try:
        rep.chat("sys", [{"role": "user", "content": [{"text": "something else"}]}], scope="s")
        assert False
    except CassetteMiss:
        pass


def test_parse_json_reply_handles_prose_and_braces_in_strings():
    assert parse_json_reply('Sure! {"say": "a {b} \\"c\\"", "done": false} ok') == {"say": 'a {b} "c"', "done": False}


def test_openai_translation_pairs_tool_calls_and_results():
    msgs = [{"role": "user", "content": [{"text": "hi"}]},
            {"role": "assistant", "content": [{"text": "checking"}, {"toolUse": {"toolUseId": "t1", "name": "x", "input": {"a": 1}}}]},
            {"role": "user", "content": [{"toolResult": {"toolUseId": "t1", "content": [{"json": {"ok": 1}}]}}]}]
    out = to_openai_messages("sys", msgs)
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool"]
    assert out[2]["tool_calls"][0]["function"]["arguments"] == json.dumps({"a": 1})


def test_agent_runs_tools_and_keeps_spoken_segments():
    replies = [
        Reply([{"text": "One moment."}, {"toolUse": {"toolUseId": "t1", "name": "verify_patient", "input": {
            "patient_full_name": "Aisha Bello", "patient_date_of_birth": "1992-05-21", "caller_is_patient": True}}}], {}, 0.4),
        Reply([{"text": "Thanks Aisha, you're verified. What day suits you?"}], {}, 0.6),
    ]
    session = CallSession(World())
    agent = Agent(V0, Scripted(replies), session)
    turn = agent.respond("Aisha Bello, May 21 1992")
    assert session.patient_id == "PT-1004"
    assert turn.segments == ["One moment.", "Thanks Aisha, you're verified. What day suits you?"]
    assert turn.llm_calls == 2 and abs(turn.latency_s - 1.0) < 1e-9


def test_barge_in_keeps_only_what_was_heard():
    agent = Agent(V0, Scripted([Reply([{"text": "I have Monday at nine or Tuesday at ten, which works?"}], {}, 0.3)]))
    agent.respond("hi")
    heard = agent.interrupt(4)
    assert heard == "I have Monday at..."
    assert agent.messages[-1]["content"] == [{"text": "I have Monday at..."}]
