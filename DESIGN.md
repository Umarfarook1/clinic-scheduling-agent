# Design note

**What it is.** Ava, a clinic phone receptionist on Claude Haiku 4.5 (small on purpose: on a call,
latency is dead air) with eight tools; an eval of 20 caller scenarios (14 train, 6 holdout, 3 calls
each); and a loop that turns failed calls into a small, gated change to her rules.

**Key choices.**
1. *Invariants in code, behaviour in the prompt.* No patient data before verification, tools that take
   no patient id, third parties only from the authorised list, no slot the search did not return, no
   booking after a red-flag symptom. The loop can only edit the prompt, so it can never weaken these.
2. *Grade the state and the trace, not the transcript.* Each call runs on a fresh clinic that the
   harness diffs, so "you're booked" is checked against the database. The LLM judge grades only what
   code cannot, quoting evidence. A transcript-only judge passed 9 of the 10 baseline calls that failed
   on state, trace or consent.
3. *The simulated caller is a witness.* It reports when it agreed to a specific slot, so "booked before
   a yes" is checked from the caller's side, not guessed from wording.
4. *Voice first.* Speakable output, three options max, speech-to-text noise, barge-in (history keeps
   only what the caller heard), and no questions spoken right before a tool call.

**How the loop works.** Evaluate; take failures from train only; the improver (Sonnet 5.5) returns at
most three typed operations (add, edit, remove a rule), each with the checks it fixes and its risk. It
cannot touch locked safety rules and can flag a failure as the eval's fault instead. Code lints the
patch (no patient names, dates, ids or scenario names). Then the full suite re-runs, train and holdout;
anything that looks worse gets three extra calls; the patch is kept only if train improves and nothing
regresses. Rejections go back to the improver with the reason.

**Before and after** (passing calls; critical = calls with a critical failure):

| | train | holdout | critical |
|---|---|---|---|
| v0 baseline | 13/42 (31%) | 5/18 (28%) | 6 |
| v1 accepted | 38/42 (90%) | 15/18 (83%) | 4 |
| v2 **rejected** | 35/42 (83%) | 15/18 (83%) | 3 |
| v3 accepted | 39/42 (93%) | 17/18 (94%) | 0 |

v2 is the interesting one. "Never use bold, even for emphasis" made Ava bold the 911 line on 6 of 6
stroke calls, and "ask the reason before the read-back" made her book on the answer to that question.
The gate caught both on extra calls; round 3 fixed the real cause (the read-back must be the only
question in its turn). Still failing: she bolds the 911 line on the allergic reaction call in every
version. That one belongs in code, not in another rule.

**One thing I would change for a real clinic.** Build the scenarios from real, de-identified calls,
and put a human between the loop and production. My callers are polite and come from my head; real
failures come from mumbled dates, kids in the background and people who change their mind three times.
The loop proposes; someone who knows the clinic approves; the patch shadow-runs before it ships.

**Where AI helped, where judgment overrode it.** I used Claude Code for implementation and first
drafts. The calls were mine: a small model on Bedrock, invariants in code out of the loop's reach, grading state
over transcripts, a strict consent check, and fixing tools in code rather than patching around them with
rules. Several first versions were wrong in ways the score hid: a regex that flagged honest
confirmations (it made the gate reject two good patches in a rehearsal), a rubric that would have
punished explaining why to call 911, a slot search that silently dropped results. Each was caught by
reading transcripts, not numbers.
