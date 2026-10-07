from frontdesk.tools import CallSession
from frontdesk.world import World


def verified(name="Maria Lopez", dob="1985-03-12"):
    s = CallSession(World())
    assert s.execute("verify_patient", {"patient_full_name": name, "patient_date_of_birth": dob,
                                         "caller_is_patient": True})["verified"]
    return s


def first_open_slot(s, visit_type="checkup", provider_id="np_fischer"):
    out = s.execute("find_available_slots", {"visit_type": visit_type, "date_from": "2026-10-19",
                                             "date_to": "2026-10-23", "provider_id": provider_id})
    return out["slots"][0]["slot_id"]


def test_patient_data_needs_verification():
    s = CallSession(World())
    out = s.execute("list_my_appointments", {})
    assert "error" in out and s.events[-1].guard == "identity"


def test_name_match_ignores_case_order_and_accents_but_not_spelling():
    s = CallSession(World())
    ok = s.execute("verify_patient", {"patient_full_name": "LOPEZ, maría", "patient_date_of_birth": "1985-03-12",
                                      "caller_is_patient": True})
    assert ok["verified"]
    s2 = CallSession(World())
    bad = s2.execute("verify_patient", {"patient_full_name": "Maria Lopes", "patient_date_of_birth": "1985-03-12",
                                        "caller_is_patient": True})
    assert bad["verified"] is False and "Lopes" not in str(bad)


def test_verification_locks_after_three_failures():
    s = CallSession(World())
    for _ in range(3):
        s.execute("verify_patient", {"patient_full_name": "Maria Lopez", "patient_date_of_birth": "1990-01-01",
                                     "caller_is_patient": True})
    out = s.execute("verify_patient", {"patient_full_name": "Maria Lopez", "patient_date_of_birth": "1985-03-12",
                                       "caller_is_patient": True})
    assert "error" in out and s.events[-1].guard == "lockout"


def test_third_party_must_be_on_the_authorised_list():
    s = CallSession(World())
    out = s.execute("verify_patient", {"patient_full_name": "Robert Chen", "patient_date_of_birth": "1958-07-30",
                                       "caller_is_patient": False, "caller_name": "Linda Chen"})
    assert out["verified"] is False and s.patient_id is None
    s = CallSession(World())
    out = s.execute("verify_patient", {"patient_full_name": "Dorothy Walsh", "patient_date_of_birth": "1941-01-09",
                                       "caller_is_patient": False, "caller_name": "karen walsh"})
    assert out["verified"] and s.patient_id == "PT-1005"


def test_book_only_slots_the_tools_returned_and_mark_them_taken():
    s = verified("Aisha Bello", "1992-05-21")
    assert "error" in s.execute("book_appointment", {"slot_id": "S-FIS-1019-0645", "visit_type": "checkup", "reason": "x"})
    assert s.events[-1].guard == "unknown_slot"
    slot = first_open_slot(s)
    assert s.execute("book_appointment", {"slot_id": slot, "visit_type": "checkup", "reason": "x"})["booked"]
    assert "error" in s.execute("book_appointment", {"slot_id": slot, "visit_type": "checkup", "reason": "x"})


def test_red_flag_blocks_booking_for_the_rest_of_the_call():
    s = verified("Aisha Bello", "1992-05-21")
    assert s.screen_caller("also I have chest pain since this morning") == "chest pain"
    out = s.execute("book_appointment", {"slot_id": first_open_slot(s), "visit_type": "checkup", "reason": "x"})
    assert "911" in out["error"] and s.events[-1].guard == "red_flag"


def test_cannot_touch_someone_elses_appointment():
    s = verified("Aisha Bello", "1992-05-21")
    out = s.execute("cancel_appointment", {"appointment_id": "A-2001"})  # Maria's
    assert "error" in out and s.events[-1].guard == "ownership"
    assert s.world.appointments["A-2001"].status == "booked"


def test_reschedule_moves_and_frees_the_old_slot():
    s = verified()
    new = first_open_slot(s, "skin_check", "dr_okafor")
    old_start = s.world.appointments["A-2001"].start
    assert s.execute("reschedule_appointment", {"appointment_id": "A-2001", "new_slot_id": new})["rescheduled"]
    assert s.world.slot_at("dr_okafor", old_start).taken is False
    assert s.world.slots[new].taken


def test_wrong_visit_type_for_provider_is_rejected():
    s = verified("Aisha Bello", "1992-05-21")
    out = s.execute("find_available_slots", {"visit_type": "skin_check", "date_from": "2026-10-19",
                                             "date_to": "2026-10-23", "provider_id": "dr_raman"})
    assert "error" in out


def test_dermatology_has_nothing_this_week_and_says_when_it_does():
    s = CallSession(World())
    out = s.execute("find_available_slots", {"visit_type": "skin_check", "date_from": "2026-10-14",
                                             "date_to": "2026-10-16", "provider_id": "dr_okafor"})
    assert out["slots"] == [] and "Earliest after that" in out["note"]


def test_fault_injection_fails_then_recovers():
    s = verified("Aisha Bello", "1992-05-21")
    s.faults = {"book_appointment": 1}
    slot = first_open_slot(s)
    assert "503" in s.execute("book_appointment", {"slot_id": slot, "visit_type": "checkup", "reason": "x"})["error"]
    assert s.execute("book_appointment", {"slot_id": slot, "visit_type": "checkup", "reason": "x"})["booked"]


def test_world_is_deterministic():
    a, b = World(), World()
    assert [(k, v.taken) for k, v in a.slots.items()] == [(k, v.taken) for k, v in b.slots.items()]


def test_search_says_when_results_were_cut_and_can_start_later():
    s = CallSession(World())
    out = s.execute("find_available_slots", {"visit_type": "sick_visit", "date_from": "2026-10-19",
                                             "date_to": "2026-10-23", "time_of_day": "afternoon"})
    assert len(out["slots"]) == 6 and out["more_available"] > 0
    late = s.execute("find_available_slots", {"visit_type": "sick_visit", "date_from": "2026-10-19",
                                              "date_to": "2026-10-23", "earliest_time": "16:00"})
    assert late["slots"] and all(("4:00 PM" in x["when"] or "4:30 PM" in x["when"]) for x in late["slots"])
    assert any("Tuesday, October 20 at 4:30 PM" == x["when"] for x in late["slots"])
