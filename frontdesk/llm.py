"""One small LLM client. Messages use the Bedrock Converse shape internally (text, toolUse and
toolResult blocks); the Anthropic and OpenAI adapters translate at the edge.

Every call can go through a cassette. In record mode each response is stored under a hash of
(scope, request); in replay mode the same request gets the same response back with no network.
That is how a reviewer without an AWS account can re-run the exact eval loop I ran.
"""
from __future__ import annotations

import hashlib
import json
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from frontdesk import config


@dataclass
class Reply:
    content: list[dict]
    usage: dict
    latency_s: float
    stop_reason: str = ""

    @property
    def text(self) -> str:
        return "".join(b["text"] for b in self.content if "text" in b).strip()

    @property
    def tool_calls(self) -> list[dict]:
        return [b["toolUse"] for b in self.content if "toolUse" in b]

    def to_json(self) -> dict:
        return {"content": self.content, "usage": self.usage, "latency_s": self.latency_s,
                "stop_reason": self.stop_reason}


class CassetteMiss(RuntimeError):
    pass


class Cassette:
    """mode: 'off' (live, nothing stored), 'record' (live, store), 'replay' (no network)."""

    def __init__(self, path: Path | None, mode: str = "off"):
        self.path, self.mode = path, mode
        self._data: dict[str, dict] = {}
        self._lock = threading.Lock()
        if path and path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self._data[row["key"]] = row["reply"]
        if mode == "replay" and not self._data:
            raise FileNotFoundError(f"Nothing to replay at {path}")

    @staticmethod
    def key(scope: str, request: dict) -> str:
        blob = json.dumps({"scope": scope, **request}, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        return self._data.get(key)

    def put(self, key: str, reply: dict) -> None:
        if self.mode != "record" or self.path is None:
            return
        with self._lock:
            self._data[key] = reply
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "reply": reply}) + "\n")


@dataclass
class Meter:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, reply: Reply) -> None:
        with self._lock:
            self.calls += 1
            self.input_tokens += reply.usage.get("inputTokens", 0)
            self.output_tokens += reply.usage.get("outputTokens", 0)
            self.seconds += reply.latency_s


RETRYABLE = {"ThrottlingException", "ServiceUnavailableException", "ModelNotReadyException",
             "InternalServerException", "ModelErrorException", "RateLimitError", "APIConnectionError",
             "InternalServerError", "OverloadedError", "APITimeoutError", "ReadTimeoutError",
             "ConnectTimeoutError", "EndpointConnectionError"}


def _error_code(e: Exception) -> str:
    resp = getattr(e, "response", None)
    if isinstance(resp, dict):
        return resp.get("Error", {}).get("Code", type(e).__name__)
    return type(e).__name__


class LLM:
    def __init__(self, role: str, model: str | None = None, temperature: float | None = 0.0,
                 max_tokens: int = 700, cassette: Cassette | None = None):
        self.role = role
        self.model = model or config.model_for(role)
        # Newer Claude models on Bedrock reject an explicit temperature.
        self.temperature = None if "sonnet-5" in self.model or "opus-5" in self.model else temperature
        self.max_tokens = max_tokens
        self.cassette = cassette or Cassette(None, "off")
        self.meter = Meter()
        self._client = None

    # ---- public --------------------------------------------------------------------------

    def chat(self, system: str, messages: list[dict], tools: list[dict] | None = None,
             scope: str = "") -> Reply:
        request = {"model": self.model, "system": system, "messages": messages,
                   "tools": tools or [], "temperature": self.temperature}
        key = Cassette.key(scope, request)
        cached = self.cassette.get(key)
        if cached is not None:
            reply = Reply(**cached)
        elif self.cassette.mode == "replay":
            raise CassetteMiss(f"No recorded response for {self.role} call in scope '{scope}'.")
        else:
            reply = self._call_with_retry(system, messages, tools)
            self.cassette.put(key, reply.to_json())
        self.meter.add(reply)
        return reply

    # ---- providers -----------------------------------------------------------------------

    def _call_with_retry(self, system, messages, tools) -> Reply:
        for attempt in range(7):
            try:
                t0 = time.time()
                content, usage, stop = getattr(self, f"_call_{config.PROVIDER}")(system, messages, tools)
                return Reply(content, usage, round(time.time() - t0, 3), stop)
            except Exception as e:  # noqa: BLE001 - provider SDKs raise many types
                if _error_code(e) not in RETRYABLE or attempt == 6:
                    raise
                time.sleep(min(30, 2 ** attempt) + random.random())
        raise RuntimeError("unreachable")

    def _call_bedrock(self, system, messages, tools):
        if self._client is None:
            import boto3
            from botocore.config import Config
            self._client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION,
                                        config=Config(connect_timeout=10, read_timeout=120,
                                                      retries={"max_attempts": 1}))
        kw = {"modelId": self.model, "system": [{"text": system}], "messages": messages,
              "inferenceConfig": {"maxTokens": self.max_tokens}}
        if self.temperature is not None:
            kw["inferenceConfig"]["temperature"] = self.temperature
        if tools:
            kw["toolConfig"] = {"tools": [{"toolSpec": {"name": t["name"], "description": t["description"],
                                                        "inputSchema": {"json": t["input_schema"]}}}
                                          for t in tools]}
        r = self._client.converse(**kw)
        content = [b for b in r["output"]["message"]["content"] if "text" in b or "toolUse" in b]
        return content, r.get("usage", {}), r.get("stopReason", "")

    def _call_anthropic(self, system, messages, tools):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        msgs = [{"role": m["role"], "content": [_to_anthropic_block(b) for b in m["content"]]} for m in messages]
        kw = {"model": self.model, "system": system, "messages": msgs, "max_tokens": self.max_tokens}
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        if tools:
            kw["tools"] = tools
        r = self._client.messages.create(**kw)
        content = []
        for b in r.content:
            if b.type == "text":
                content.append({"text": b.text})
            elif b.type == "tool_use":
                content.append({"toolUse": {"toolUseId": b.id, "name": b.name, "input": b.input}})
        usage = {"inputTokens": r.usage.input_tokens, "outputTokens": r.usage.output_tokens}
        return content, usage, r.stop_reason or ""

    def _call_openai(self, system, messages, tools):
        if self._client is None:
            import openai
            self._client = openai.OpenAI()
        kw = {"model": self.model, "messages": to_openai_messages(system, messages)}
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        if tools:
            kw["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                             "parameters": t["input_schema"]}} for t in tools]
        r = self._client.chat.completions.create(**kw)
        msg = r.choices[0].message
        content = [{"text": msg.content}] if msg.content else []
        for tc in msg.tool_calls or []:
            content.append({"toolUse": {"toolUseId": tc.id, "name": tc.function.name,
                                        "input": json.loads(tc.function.arguments or "{}")}})
        usage = {"inputTokens": r.usage.prompt_tokens, "outputTokens": r.usage.completion_tokens}
        return content, usage, r.choices[0].finish_reason or ""


def _to_anthropic_block(b: dict) -> dict:
    if "text" in b:
        return {"type": "text", "text": b["text"]}
    if "toolUse" in b:
        t = b["toolUse"]
        return {"type": "tool_use", "id": t["toolUseId"], "name": t["name"], "input": t["input"]}
    t = b["toolResult"]
    return {"type": "tool_result", "tool_use_id": t["toolUseId"],
            "content": json.dumps(t["content"][0]["json"]), "is_error": t.get("status") == "error"}


def to_openai_messages(system: str, messages: list[dict]) -> list[dict]:
    out: list[dict] = [{"role": "system", "content": system}]
    for m in messages:
        texts = [b["text"] for b in m["content"] if "text" in b]
        if m["role"] == "assistant":
            calls = [{"id": b["toolUse"]["toolUseId"], "type": "function",
                      "function": {"name": b["toolUse"]["name"], "arguments": json.dumps(b["toolUse"]["input"])}}
                     for b in m["content"] if "toolUse" in b]
            msg = {"role": "assistant", "content": "\n".join(texts) or None}
            if calls:
                msg["tool_calls"] = calls
            out.append(msg)
        else:
            for b in m["content"]:
                if "toolResult" in b:
                    out.append({"role": "tool", "tool_call_id": b["toolResult"]["toolUseId"],
                                "content": json.dumps(b["toolResult"]["content"][0]["json"])})
            if texts:
                out.append({"role": "user", "content": "\n".join(texts)})
    return out


def parse_json_reply(text: str) -> dict:
    """Pull the first JSON object out of a model reply (models like to wrap it in prose or fences)."""
    start = text.find("{")
    if start < 0:
        raise ValueError(f"No JSON object in reply: {text[:200]}")
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError(f"Unbalanced JSON in reply: {text[:200]}")
