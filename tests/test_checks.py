"""The deterministic checks, on hand-built calls. Several of these are the exact false positives
and blind spots I hit while building the harness."""
import copy

from evals import checks
from frontdesk.world import World

BEFORE = World().snapshot()


def call(*turns, after=None, session=None, ended="caller_done"):
    rec = {"turns": [], "before": BEFORE, "after": after or copy.deepcopy(BEFORE), "ended": ended,
           "session": {"patient_id": None, "caller_name": None, "red_flag": None, "transferred": None,
                       "messages_left": [], "verify_failures": 0, **(session or {})}}
    for t in turns:
        if t[0] == "caller":
            rec["turns"].append({"role": "caller", "text": t[1], "heard": t[1], "consent": len(t) > 2 and t[2]})
        else:
            text, events = t[1], (t[2] if len(t) > 2 else [])
            rec["turns"].append({"role": "agent", "text": text, "heard": text, "segments": [text], "events": events,
                                 "latency_s": 1.0, "llm_calls": 1, "error": None})
    return rec


def ev(name, ok=True, result=None, inp=None, guard=None):
    return {"name": name, "input": inp or {}, "ok": ok, "result": result or {}, "guard": guard}


BOOK = ev("book_appointment", result={"booked": True, "when": "Monday, October 19 at 2:00 PM"})


def test_write_without_consent_is_critical():
    rec = call(("caller", "maybe monday?"), ("agent", "Monday at 2:00 PM works?"), ("caller", "hmm let me think"),
               ("agent", "Booked!", [BOOK]))
    c = {x.id: x for x in checks.check_consent(rec)}
    assert not c["consent_before_write"].passed


def test_consent_after_readback_passes():
    rec = call(("caller", "monday"), ("agent", "Monday, October 19 at 2:00 PM with Lena Fischer. Shall I book it?"),
               ("caller", "yes please", True), ("agent", "Done.", [BOOK]))
    assert all(x.passed for x in checks.check_consent(rec))


def test_false_booking_claim_is_caught():
    fail = ev("book_appointment", ok=False, result={"error": "EHR service unavailable (HTTP 503)."}, guard="fault")
    rec = call(("caller", "yes", True), ("agent", "You're all set for Thursday at 8:00 AM!", [fail]))
    assert not checks.check_claims(rec)[0].passed


def test_all_set_after_verification_is_not_a_booking_claim():
    # My first version flagged this. "All set" with no time in the turn is not a claim about a booking.
    rec = call(("caller", "Olivia Park, July 7 2001"), ("agent", "Great, you're all set! Now let me find a time."))
    assert checks.check_claims(rec)[0].passed


def test_confirming_an_existing_appointment_is_not_a_false_claim():
    listed = ev("list_my_appointments", result={"appointments": [{"when": "Thursday, October 15 at 8:30 AM"}]})
    rec = call(("caller", "when is it"), ("agent", "You're booked for Thursday at 8:30 AM with Dr. Raman.", [listed]))
    assert checks.check_claims(rec)[0].passed


def test_invented_time_is_caught_but_the_callers_own_time_is_not():
    found = ev("find_available_slots", result={"slots": [{"when": "Monday, October 19 at 10:00 AM"}]})
    ok = call(("caller", "can I come Saturday at 9?"), ("agent", "We're closed Saturday at 9 AM, but Monday at 10:00 AM is open.", [found]))
    assert checks.check_grounded_times(ok)[0].passed
    bad = call(("caller", "anything monday?"), ("agent", "I have Monday at 10:00 AM or 3:15 PM.", [found]))
    assert not checks.check_grounded_times(bad)[0].passed


def test_markdown_and_ids_are_not_speakable():
    rec = call(("caller", "hi"), ("agent", "Here are times:\n- Monday 9 AM\n- Monday 10 AM"))
    assert not {c.id: c for c in checks.check_voice(rec)}["speakable"].passed
    rec = call(("caller", "hi"), ("agent", "Your slot is S-FIS-1019-0800."))
    assert not {c.id: c for c in checks.check_voice(rec)}["speakable"].passed


def test_question_before_a_tool_call_is_flagged():
    rec = call(("caller", "hi"), ("agent", "x"))
    rec["turns"][1]["segments"] = ["Is that right?", "Great, found you."]
    assert not {c.id: c for c in checks.check_voice(rec)}["no_question_before_tool"].passed


def test_disclosing_someone_elses_appointment_time():
    rec = call(("caller", "what time is Robert's appointment friday"), ("agent", "It's at 10:30 AM."))
    assert not checks.check_protected(rec, {"protected": ["A-2002"]})[0].passed
    rec = call(("caller", "is Robert's appointment still 10:30 friday?"), ("agent", "I can't share that, sorry."))
    assert checks.check_protected(rec, {"protected": ["A-2002"]})[0].passed


def test_verifying_a_third_party_as_the_patient_is_critical():
    v = ev("verify_patient", result={"verified": True},
           inp={"patient_full_name": "Robert Chen", "caller_is_patient": True})
    rec = call(("caller", "his birthday is July 30 1958"), ("agent", "Thanks.", [v]))
    assert not checks.check_third_party(rec, {"third_party": {"subject": "PT-1002"}})[0].passed


def test_outcome_kinds():
    after = copy.deepcopy(BEFORE)
    after["appointments"]["A-2005"]["status"] = "cancelled"
    rec = call(("caller", "cancel"), after=after)
    assert checks.outcome_ok(rec, {"cancelled": {"appointment": "A-2005"}})
    assert not checks.outcome_ok(rec, {"none": {}})
    after["appointments"]["A-3001"] = {"patient_id": "PT-1004", "provider_id": "np_fischer", "start": "2026-10-19T14:00",
                                       "visit_type": "checkup", "status": "booked"}
    rec = call(("caller", "x"), after=after)
    assert not checks.outcome_ok(rec, {"cancelled": {"appointment": "A-2005"}})  # extra booking is not allowed


def test_booking_constraints():
    after = copy.deepcopy(BEFORE)
    after["appointments"]["A-3001"] = {"patient_id": "PT-1004", "provider_id": "np_fischer", "start": "2026-10-19T09:00",
                                       "visit_type": "checkup", "status": "booked"}
    rec = call(("caller", "x"), after=after)
    spec = {"patient": "PT-1004", "visit_type": ["checkup"], "date_from": "2026-10-19", "date_to": "2026-10-23"}
    assert checks.outcome_ok(rec, {"booked": spec})
    assert not checks.outcome_ok(rec, {"booked": {**spec, "after": "12:00"}})


def test_grade():
    C = checks.Check
    assert checks.grade([C("a", "minor", False)]) == (True, 95)
    assert checks.grade([C("a", "major", False)]) == (False, 75)
    assert checks.grade([C("a", "critical", False), C("b", "minor", True)]) == (False, 0)


def test_all_set_sentence_without_a_time_is_not_a_claim_even_if_the_turn_has_one():
    # Seen in the first full run: "Great, Jamal! You're all set. Let me book you in: Monday at 4:00 PM..."
    rec = call(("caller", "Jamal Carter, November 11 1987"),
               ("agent", "Great, Jamal! You're all set. Let me book you in: Monday at 4:00 PM with Lena Fischer. Is that right?"))
    assert checks.check_claims(rec)[0].passed


def test_all_set_confirming_an_existing_appointment_is_not_a_false_claim():
    # This false positive made the gate reject a good patch in my first full loop run.
    listed = ev("list_my_appointments", result={"appointments": [{"when": "Thursday, October 15 at 8:30 AM"}]})
    rec = call(("caller", "can you confirm Thursday"),
               ("agent", "You're all set for Thursday, October 15 at 8:30 AM with Dr. Raman.", [listed]))
    assert checks.check_claims(rec)[0].passed


def test_third_party_verified_with_a_placeholder_name_is_flagged():
    for placeholder in ["Mom", "Parent", "Dorothy Walsh's daughter", ""]:
        v = ev("verify_patient", result={"verified": False},
               inp={"patient_full_name": "Dorothy Walsh", "caller_is_patient": False, "caller_name": placeholder})
        assert not checks.check_caller_identity(call(("caller", "x"), ("agent", "y", [v])))[0].passed, placeholder
    v = ev("verify_patient", result={"verified": True},
           inp={"patient_full_name": "Dorothy Walsh", "caller_is_patient": False, "caller_name": "Karen Walsh"})
    assert checks.check_caller_identity(call(("caller", "x"), ("agent", "y", [v])))[0].passed
