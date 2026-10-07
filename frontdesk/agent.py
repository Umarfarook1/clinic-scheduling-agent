"""The agent loop: one caller utterance in, one spoken reply out, with tool calls in between.

Conversation state lives in two places on purpose. The message history is what the model
sees. The CallSession is what the clinic knows: who was verified, whether a red flag fired,
what was booked. The model can be confused about the first; it cannot change the second
except through a tool, and the tools check it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from frontdesk.llm import LLM
from frontdesk.policy import Policy
from frontdesk.tools import TOOL_SPECS, CallSession, ToolEvent

MAX_TOOL_ROUNDS = 6
FALLBACK_LINE = "Sorry, I didn't catch that. Could you say it again?"


@dataclass
class AgentTurn:
    text: str
    segments: list[str] = field(default_factory=list)  # text spoken before each tool round, then the final reply
    events: list[ToolEvent] = field(default_factory=list)
    llm_calls: int = 0
    latency_s: float = 0.0
    error: str | None = None


class Agent:
    def __init__(self, policy: Policy, llm: LLM, session: CallSession | None = None):
        self.policy = policy
        self.system = policy.compile()
        self.llm = llm
        self.session = session or CallSession()
        self.messages: list[dict] = []
        self._turn_start = 0

    def respond(self, caller_text: str, scope: str = "") -> AgentTurn:
        s = self.session
        s.turn += 1
        self._turn_start = len(self.messages)
        content = caller_text
        hit = s.screen_caller(caller_text)
        if hit:
            content += (f"\n\n[Safety screen: the caller mentioned \"{hit}\". "
                        "Treat this as a possible medical emergency.]")
        self.messages.append({"role": "user", "content": [{"text": content}]})

        turn = AgentTurn(text="")
        spoken: list[str] = []
        n_events = len(s.events)
        for _ in range(MAX_TOOL_ROUNDS):
            reply = self.llm.chat(self.system, self.messages, TOOL_SPECS, scope=scope)
            turn.llm_calls += 1
            turn.latency_s += reply.latency_s
            blocks = reply.content or [{"text": FALLBACK_LINE}]
            if not reply.content:
                turn.error = "empty_reply"
            self.messages.append({"role": "assistant", "content": blocks})
            if reply.text:
                spoken.append(reply.text)
            if not reply.tool_calls:
                break
            results = []
            for call in reply.tool_calls:
                out = s.execute(call["name"], call.get("input") or {})
                results.append({"toolResult": {"toolUseId": call["toolUseId"], "content": [{"json": out}],
                                               "status": "error" if "error" in out else "success"}})
            self.messages.append({"role": "user", "content": results})
        else:
            turn.error = "tool_loop"
            spoken.append(FALLBACK_LINE)
            self.messages.append({"role": "assistant", "content": [{"text": FALLBACK_LINE}]})

        turn.segments = spoken
        turn.text = " ".join(spoken).strip() or FALLBACK_LINE
        turn.events = s.events[n_events:]
        turn.latency_s = round(turn.latency_s, 3)
        return turn

    def interrupt(self, keep_words: int) -> str:
        """The caller talked over the reply. Like a real voice stack, keep only what was heard
        in the history, so the model knows the rest never reached the caller."""
        budget = keep_words
        heard: list[str] = []
        for msg in self.messages[self._turn_start:]:
            if msg["role"] != "assistant":
                continue
            kept = []
            for b in msg["content"]:
                if "text" not in b:
                    kept.append(b)
                    continue
                words = b["text"].split()
                take, budget = words[:budget], max(0, budget - len(words))
                if take:
                    cut = " ".join(take) + ("..." if len(take) < len(words) else "")
                    kept.append({"text": cut})
                    heard.append(cut)
            msg["content"] = kept or [{"text": "..."}]
        return " ".join(heard)
