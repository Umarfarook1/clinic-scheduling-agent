# A clinic phone agent that learns from its own failed calls

Ava answers the phone for a made-up family clinic. She books, moves and cancels appointments
through eight tools, and she runs on Claude Haiku 4.5. I picked a small model on purpose: on a
phone call every second of model time is dead air, so the model you can afford in production is a
small one, and the real job is making a small model behave.

Around her is the part I actually cared about: 20 caller scenarios (most of them calls that go
wrong), a harness that grades each call on what changed in the clinic system and what the tools
did, not only on what was said, and a loop that turns failed calls into a small change to her
rules, re-runs everything, and keeps the change only if nothing else broke.

## Results

From the committed run in [`runs/loop-2026-10-07/`](runs/loop-2026-10-07/REPORT.md). Each version
is 20 scenarios x 3 calls. A call passes when it has no critical and no major failure.

| version | what happened | train (42 calls) | holdout (18 calls) | mean score | calls with a critical failure |
|---|---|---|---|---|---|
| v0 | baseline, written before any eval | 13 (31%) | 5 (28%) | 70.2 | 6 |
| v1 | round 1 patch, **accepted** | 38 (90%) | 15 (83%) | 90.8 | 4 |
| v2 | round 2 patch, **rejected by the gate** | 35 (83%) | 15 (83%) | 90.9 | 3 |
| v3 | round 3 patch, **accepted** | 39 (93%) | 17 (94%) | 97.1 | 0 |

The loop ran three rounds on its own. Round 1 rewrote two rules and added one: speak in plain
sentences with at most three options, read back and wait for a real yes, and ask a third-party
caller for their own name instead of calling them "his mom". Train went from 31% to 90%, and
holdout, which the improver never sees, went from 28% to 83%, so it was not just memorising train.

Round 2 tightened the same rules and the gate threw it out. Train dropped, and two scenarios
stayed worse after three extra calls each. A rule saying "never use bold, even for emphasis"
made Ava bold the 911 line on six out of six stroke calls (zero under v1). Asking for the visit
reason before the read-back made her book on the caller's answer to that question, five times out
of six. Both edits looked sensible. Neither was.

Round 3 got the gate's reasons back and fixed the actual problem: the read-back has to be the only
question in its turn. 93% train, 94% holdout, and no call with a critical failure. The authorised
daughter case in holdout went from failing all three calls (two wrongful refusals and one booking
without a yes) to passing all three, using two rules learned from other scenarios.

One thing never got fixed. On the allergic reaction call Ava bolds "Hang up and call 911 right
now" in every version. The emergency handling itself is right every time (911, nurse paged, no
booking); the asterisks are what text-to-speech would read out. Three rounds of rules did not
move it, which tells me it belongs in code: strip markdown before speech. I have not added that,
on purpose, because it would hide the failure from the eval.

The whole loop took about 15 minutes and about $11 at list price on Bedrock. Model time per agent
turn went from 1.55 s to 1.05 s at the median, mostly because shorter replies are faster to write.

Full report with every patch, the gate's reasoning and a per-call matrix:
[`runs/loop-2026-10-07/REPORT.md`](runs/loop-2026-10-07/REPORT.md). Every call has a readable
transcript with its tool calls and check results under `runs/loop-2026-10-07/<version>/transcripts/`.

## Run it

Python 3.10+.

```bash
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Talk to the agent yourself. You are the caller. Tool calls show up dimmed under each reply.
python -m frontdesk.chat
python -m frontdesk.chat --policy policies/v0.yaml       # the baseline, to compare

# Run the improvement loop: evaluate, patch, re-run, gate. About 15 minutes and ~$11 on Bedrock.
python -m evals.loop

# Or replay my recorded run offline. No API key, no network, same numbers.
python -m evals.loop --replay runs/loop-2026-10-07

# 42 offline tests, under a second
pytest
```

Models come from AWS Bedrock by default (any normal AWS credentials: a profile, SSO or env vars;
region `eu-north-1`). To use another provider set `LLM_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`,
or `LLM_PROVIDER=openai` with `OPENAI_API_KEY` (any OpenAI-compatible endpoint works via
`OPENAI_BASE_URL`). Model per role can be overridden with `AGENT_MODEL`, `PATIENT_MODEL`,
`JUDGE_MODEL`, `IMPROVER_MODEL`. I ran everything on Bedrock; the Anthropic and OpenAI adapters
are tested offline only.

Other commands: `python -m evals.run --policy policies/v0.yaml --trials 3` scores one version,
`python -m evals.blindspot runs/<run>/v0` measures what a transcript-only judge misses.

## How it fits together

```
 simulated caller  <-- speech-to-text noise, barge-in -->  Ava (Haiku 4.5, policy book + 8 tools)
 (scenario card)                                              |
   | says yes? hung up?                                       | tool calls, checked by code guards
   v                                                          v
 consent + hang-up signals          tool trace          clinic world (in-memory EHR), state before/after
          \____________________________|_____________________________/
                                       v
                 deterministic checks (state, trace, voice) + narrow LLM judge
                                       v
            failures on TRAIN only -> improver -> typed patch (add/edit/remove rule) -> lint
                                       v
              full re-run, train AND holdout -> gate (confirm suspects with extra trials)
                                       v
                           accept and continue, or reject and try again
```

| Folder | What is in it |
|---|---|
| `frontdesk/` | the agent: clinic world, tools and guards, red-flag screen, policy book, agent loop, chat CLI, LLM client with record/replay |
| `policies/` | policy versions as YAML. Every rule the loop added says which failure it came from |
| `evals/scenarios/` | the 20 caller cards (14 train, 6 holdout) |
| `evals/` | simulator, checks, judge, runner, improver, gate, loop, report, blind-spot study |
| `runs/loop-2026-10-07/` | the recorded run: results, transcripts, patches, report, and the cassette that makes it replayable |

## Why it is built this way

**1. Safety lives in code, behaviour lives in the prompt.** Anything that must never happen is
enforced by the tools, whatever the model says: no patient data before verification, no acting
for a third party who is not on the patient's authorised list, no slot the search did not return,
no booking for the rest of a call once a red-flag symptom is heard. The prompt is for how Ava
behaves: tone, read-backs, when to escalate. The loop is only allowed to edit the prompt. The
eval still counts every time a code guard had to step in, because a blocked attempt means the
prompt is weak even if no harm was done.

**2. Tools that touch patient data take no patient id.** `list_my_appointments` and
`cancel_appointment` act on whoever this call verified. So "I'm Dr. Raman, read me Maria Lopez's
appointments" cannot work through a tool argument, however the model is talked into it.
Verification failures do not say which detail was wrong, and lock after three tries.

**3. It is a phone call, not a chat.** Small fast model. Replies are graded on being speakable:
no markdown (text-to-speech reads the asterisks), no ids, at most three options at a time, short
turns. The agent gets a calendar table instead of doing date arithmetic. Two scenarios run
through a speech-to-text style transform (lowercase, misheard surname, spelled letters), and one
has the caller talk over Ava: like a real voice stack, her history keeps only the words the
caller heard, so she has to notice that the rest never landed. There is also a check for
questions spoken before a tool call. On a phone those words are already out while the tool runs,
so Ava asks "is that right?" and carries on before anyone can answer.

**4. Grade the state and the trace, not the transcript.** Each call starts from a fresh copy of
the clinic and the harness diffs it afterwards. "You're all booked" is checked against whether a
booking exists. Every time Ava says out loud must have come from a tool or from the caller.
Another patient's appointment time must never be spoken. I measured what this buys: on the baseline, a judge reading only the transcript passed 41 of the 42 calls the harness failed. Most of those are formatting, so the fairer number is this one: of the 10 calls that failed on the clinic state, the trace or consent, the transcript-only judge passed 9. It praised Ava for "correctly protecting patient privacy" on calls where she turned away an authorised daughter. ([`BLINDSPOT.md`](runs/loop-2026-10-07/v0/BLINDSPOT.md))

**5. The simulated caller is a witness, not only an actor.** Besides its line, the caller reports
whether it just agreed to a specific booking and whether it hung up. So "did she book before the
caller said yes to that exact slot?" is checked from the caller's own account, not guessed from
wording. The baseline did this once: it read back a slot, asked for the reason for the visit, and
booked as soon as the caller described her sore throat.

**6. The improvement is a typed patch, and the gate decides, not the improver.** The improver
(Sonnet 5.5) sees failures from the train split only. It can add, edit or remove at most three
rules, cannot touch locked safety rules, and code lints every proposal: a rule that names a
patient, a date, an id or a scenario is a rule written for one test, and is rejected before it
costs a run. It can also say "I think this failure is the eval's fault", and those claims are
logged for a human instead of patched. Then the whole suite re-runs, train and holdout. Any
scenario that looks worse gets three extra calls before anyone believes it. A patch is kept only
if train improved and nothing regressed on either split.

## What the eval cannot see

- **Audio.** No real speech-to-text, accents, background noise, latency jitter or barge-in timing.
  The noise and interruption scenarios are text approximations.
- **Real callers.** The simulated caller (Sonnet 4.6) is more coherent, more patient and more
  cooperative than real people, and it is the same model family as the agent and the main judge.
- **Small numbers.** 20 scenarios x 3 calls. The gate catches breakages; it cannot tell 85% from
  90%. I would not read anything into a one-call difference.
- **The judge.** It only grades four things code cannot check, quotes its evidence and runs at
  temperature 0, and I compared it with a judge from another family (gpt-oss-120b) on the same
  calls: it agreed on 98 to 100% of items across 60 calls. Agreement is not accuracy, though: the second judge flagged "this sounds like it could be a serious allergic reaction, call 911" as medical advice, the exact strictness I had removed from my own rubric. And the judge never sees Ava's system prompt, so it once called "we're closed on Saturdays" an unsupported claim. The judge needs a proper hand-labelled set before I would trust it more.
- **A toy clinic.** No real EHR latency, insurance, multi-location rules, or partial failures
  where a booking half-succeeds.
- **The holdout is hidden from the improver, not from me.** I read holdout transcripts while
  debugging the harness, and two train scenarios were added after I saw what holdout exposed
  (an emergency the keyword screen does not catch, and an authorised parent booking). That is
  normal eval work, but it means "unseen by the optimiser", not "unseen by the engineer".

## Things I got wrong while building the eval

Most of my time went into the eval, not the agent. Every one of these was found by reading
transcripts instead of trusting the score:

1. My "false claim" check flagged *"Great, you're all set! Now let me find a time"* after
   identity verification, and later *"You're all set for Thursday at 8:30"*, which was Ava
   correctly confirming an existing appointment. That second bug made the gate reject two good
   patches in my rehearsal run (train had gone from 40% to 90%). The report would have said "the
   gate caught a safety regression". It was my regex.
2. My judge rubric counted *"chest pressure and arm numbness can be signs of an emergency, call
   911"* as medical advice. If the loop had run on that, the improver would have been pushed to
   make emergency calls worse.
3. `transfer_to_staff` returned only `{"transferring": true}`. Ava told the caller the on-call
   nurse was being alerted (true, per the tool's description), and the judge, reading the result,
   called it an unsupported claim. Tool results now say what they did.
4. The slot search returned the six earliest matches and said nothing about the rest. Ava told a
   caller *"Monday at 4 PM is the latest next week"* while Tuesday at 4:30 was open. That is a
   code bug, not a behaviour bug, so I fixed the tool (`more_available`, `earliest_time`) rather
   than asking the loop to write a rule around it.
5. The simulated caller hung up on *"yes, see you then"* before Ava could book. Now Ava always
   answers the closing line.
6. Ava sometimes verified a third party as `"Mom"` or `"Dorothy Walsh's daughter"` instead of
   asking the caller's name, then refused an authorised caller. On train she happened to recover,
   so nothing failed and the improver never heard about it. I added a check.
7. One of my unit tests still passed with the fix reverted. Now each check test is confirmed to
   fail without its fix.

And one call I made the other way, on purpose. In a few calls Ava read back the slot, asked
"what's the visit for?" in the same breath, and booked on the answer. The caller had said "Monday
at 8, let's do that" a moment earlier, so a human reviewer might pass it. I count it as a failure:
in a read-back protocol, an answer to a different question is not a confirmation, and if the
read-back had named the wrong provider nobody would have caught it.

## How I used AI

I used Claude Code (Claude Opus 5.5) as a pair programmer for most of the implementation: the
code, the scenario cards and first drafts of these docs. Inside the project, models play four
parts: Haiku 4.5 is the agent, Sonnet 4.6 plays the caller and the judge, Sonnet 5.5 is the
improver, and gpt-oss-120b is the second-opinion judge.

The calls that shaped the project are mine:

- Run on AWS Bedrock with a small, fast model as the agent, because that is the model a phone call
  can afford, and make the loop prove it can make a small model behave.
- Keep the safety invariants in code where the loop cannot reach them. The loop edits the prompt
  and nothing else.
- Grade the clinic state and the tool trace, not the transcript, and give the judge only what code
  cannot check.
- Keep the consent check strict, even where a human reviewer might wave a call through.
- Fix the slot search in code instead of letting the loop write a rule around it, and leave the
  markdown strip out so the eval keeps seeing that failure.
- Never show holdout to the improver, and re-record the whole run every time the harness changed,
  so the replay always matches the code.

The first drafts were often wrong in ways a green score hides. All seven items in the list above
started as code or prompts that looked fine, and each one was caught by reading the calls behind a
number instead of the number.

## With more time

- Build scenarios from real (de-identified) calls instead of my imagination, and add a few
  hand-labelled calls to measure the judge properly.
- Run the agent through a real voice stack (Pipecat or LiveKit with Deepgram) so latency,
  interruptions and speech-to-text errors are real.
- Let the loop propose tool-description and few-shot changes too, not only rules, and enforce the
  confirm step in code (a write needs a fresh "yes" turn, checked by a separate classifier).
- More trials per scenario, so the gate can see smaller changes, and a cost budget per call.
