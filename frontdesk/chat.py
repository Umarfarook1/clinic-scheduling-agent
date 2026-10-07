"""Talk to the agent yourself: you are the caller.

    python -m frontdesk.chat                      # latest accepted policy
    python -m frontdesk.chat --policy policies/v0.yaml
    python -m frontdesk.chat --script demo/call.txt   # play scripted caller lines (for recordings)

Tool calls are shown dimmed under each reply, so you can see what the agent actually did,
not only what it said. Type /state to see the appointment changes so far, /quit to hang up.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from rich.console import Console

from frontdesk.agent import Agent
from frontdesk.config import POLICIES_DIR
from frontdesk.llm import LLM
from frontdesk.policy import GREETING, Policy
from frontdesk.tools import CallSession
from frontdesk.world import World

console = Console(highlight=False)


def latest_policy() -> Path:
    return sorted(POLICIES_DIR.glob("v*.yaml"), key=lambda p: int(p.stem[1:]))[-1]


def show_events(events) -> None:
    for e in events:
        args = json.dumps(e.input, ensure_ascii=False)
        res = json.dumps(e.result, ensure_ascii=False)
        tag = "[red]blocked[/red] " if e.guard else ""
        console.print(f"   [dim]-> {e.name}({args})[/dim]")
        console.print(f"   [dim]<- {tag}{res[:300]}{'...' if len(res) > 300 else ''}[/dim]")


def state_diff(before: dict, after: dict) -> list[str]:
    out = []
    for aid, a in after["appointments"].items():
        b = before["appointments"].get(aid)
        if b is None:
            out.append(f"NEW {aid}: {a['patient_id']} with {a['provider_id']} at {a['start']} ({a['visit_type']})")
        elif b != a:
            out.append(f"CHANGED {aid}: {b['start']} {b['status']} -> {a['start']} {a['status']}")
    return out or ["no changes"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", type=Path, default=None)
    ap.add_argument("--script", type=Path, default=None, help="caller lines, one per line")
    ap.add_argument("--pace", type=float, default=0.04, help="typing delay per character in --script mode")
    args = ap.parse_args()

    policy = Policy.load(args.policy or latest_policy())
    session = CallSession(World())
    before = session.world.snapshot()
    agent = Agent(policy, LLM("agent"), session)
    script = args.script.read_text(encoding="utf-8").splitlines() if args.script else None

    console.print(f"[bold]Maple Street Family Clinic[/bold]  (policy {policy.version}, "
                  f"{len(policy.rules)} rules, model {agent.llm.model})")
    console.print("[dim]You are the caller. /state shows changes, /quit hangs up.[/dim]\n")
    console.print(f"[bold cyan]Ava:[/bold cyan] {GREETING}")
    while True:
        if script is not None:
            if not script:
                break
            line = script.pop(0).strip()
            console.print("[bold green]You:[/bold green] ", end="")
            for ch in line:
                console.print(ch, end="")
                time.sleep(args.pace)
            console.print()
        else:
            line = console.input("[bold green]You:[/bold green] ").strip()
        if not line:
            continue
        if line == "/quit":
            break
        if line == "/state":
            for row in state_diff(before, session.world.snapshot()):
                console.print(f"   [yellow]{row}[/yellow]")
            continue
        turn = agent.respond(line)
        show_events(turn.events)
        console.print(f"[bold cyan]Ava:[/bold cyan] {turn.text}  [dim]({turn.latency_s:.1f}s)[/dim]\n")
        if session.transferred:
            console.print(f"[magenta]-- call handed to staff (urgency: {session.transferred}) --[/magenta]")
            break
    console.print("\n[bold]What changed in the clinic system:[/bold]")
    for row in state_diff(before, session.world.snapshot()):
        console.print(f"   [yellow]{row}[/yellow]")


if __name__ == "__main__":
    main()
