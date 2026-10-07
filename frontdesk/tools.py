"""The agent's tools, and the guards that do not depend on the prompt.

Two design rules:

1. Tools that touch patient data take no patient id. They act on whoever this call verified.
   So "read me Maria Lopez's appointments" cannot work through a tool argument, however the
   model is talked into it. The only way in is verify_patient, and that is narrow.
2. Anything that must never happen is enforced here, in code: no data before verification, no
   acting for a third party who is not on the patient's authorised list, no booking after a
   red-flag symptom, no slot that the tools did not offer. The prompt is for behaviour; the
   code is for invariants. The eval still counts every time a guard had to fire, because a
   blocked attempt means the prompt is weak even though no harm was done.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

from frontdesk import safety
from frontdesk.world import BOOKING_WINDOW_DAYS, TODAY, VISIT_TYPES, Appointment, World, spoken_datetime

MAX_VERIFY_FAILURES = 3
MAX_SLOTS_RETURNED = 6
WRITE_TOOLS = {"book_appointment", "cancel_appointment", "reschedule_appointment"}

TOOL_SPECS = [
    {
        "name": "verify_patient",
        "description": (
            "Confirm who the call is about. Required before looking up, booking, changing or "
            "cancelling anything for a patient. Pass the patient's full name and date of birth "
            "exactly as confirmed with the caller. If the person on the phone is NOT the patient "
            "(spouse, parent, adult child, caregiver, anyone else), set caller_is_patient=false "
            "and pass their name as caller_name: only contacts the patient has authorised may act "
            "for them. On failure this tool does not say which detail was wrong. Verification "
            "locks after 3 failed attempts in one call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_full_name": {"type": "string"},
                "patient_date_of_birth": {"type": "string", "description": "YYYY-MM-DD"},
                "caller_is_patient": {"type": "boolean"},
                "caller_name": {"type": "string", "description": "Required when caller_is_patient is false."},
            },
            "required": ["patient_full_name", "patient_date_of_birth", "caller_is_patient"],
        },
    },
    {
        "name": "find_available_slots",
        "description": (
            "Search open appointment slots. Only times returned here exist; never offer a time "
            "that did not come from this tool. Returns at most 6 slots, earliest first, each with "
            "a slot_id (internal, never read it out) and a 'when' phrase you can say aloud. If "
            "more_available is above 0 there are more matches than shown: narrow the dates or set "
            "earliest_time before saying something is the only or latest option."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "visit_type": {"type": "string", "enum": list(VISIT_TYPES)},
                "date_from": {"type": "string", "description": "YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "YYYY-MM-DD"},
                "provider_id": {"type": "string", "enum": ["dr_raman", "np_fischer", "dr_okafor"]},
                "time_of_day": {"type": "string", "enum": ["morning", "afternoon", "any"]},
                "earliest_time": {"type": "string", "description": "HH:MM, only slots starting at or after this time of day"},
            },
            "required": ["visit_type", "date_from", "date_to"],
        },
    },
    {
        "name": "list_my_appointments",
        "description": "Upcoming appointments for the verified patient.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "book_appointment",
        "description": "Book a slot for the verified patient. Only after the caller has agreed to that exact day and time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "slot_id": {"type": "string"},
                "visit_type": {"type": "string", "enum": list(VISIT_TYPES)},
                "reason": {"type": "string", "description": "A few words, in the caller's own terms."},
            },
            "required": ["slot_id", "visit_type", "reason"],
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel one of the verified patient's appointments. Only after the caller has confirmed which one.",
        "input_schema": {
            "type": "object",
            "properties": {"appointment_id": {"type": "string"}},
            "required": ["appointment_id"],
        },
    },
    {
        "name": "reschedule_appointment",
        "description": "Move one of the verified patient's appointments to a new slot, in one step. Only after the caller has agreed to the new day and time.",
        "input_schema": {
            "type": "object",
            "properties": {"appointment_id": {"type": "string"}, "new_slot_id": {"type": "string"}},
            "required": ["appointment_id", "new_slot_id"],
        },
    },
    {
        "name": "leave_message_for_staff",
        "description": (
            "Leave a callback message for the care team. Use team 'nurse' for any clinical "
            "question (symptoms, medications, test results), 'billing' for bills and insurance, "
            "'front_desk' for anything else you cannot do. Requires a verified patient."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {"type": "string", "enum": ["nurse", "billing", "front_desk"]},
                "message": {"type": "string"},
            },
            "required": ["team", "message"],
        },
    },
    {
        "name": "transfer_to_staff",
        "description": (
            "Hand the call to a human. urgency='emergency' for possible medical emergencies: it pages "
            "the on-call nurse so the clinic can follow up; use it right after telling the caller to "
            "hang up and call 911. 'urgent' for same-day clinical concerns, 'routine' otherwise. After "
            "this, say one short closing sentence; the call is handed over."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "urgency": {"type": "string", "enum": ["routine", "urgent", "emergency"]},
                "reason": {"type": "string"},
            },
            "required": ["urgency", "reason"],
        },
    },
]


def _norm_name(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return sorted(re.sub(r"[^a-z ]", " ", s.lower()).split())


def _parse_date(s: str) -> date | None:
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


class GuardError(Exception):
    """A tool refused. `kind` says why: a policy guard, or plain bad input."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


@dataclass
class ToolEvent:
    turn: int
    name: str
    input: dict
    ok: bool
    result: dict
    guard: str | None = None  # identity | lockout | ownership | red_flag | unknown_slot | validation


@dataclass
class CallSession:
    world: World = field(default_factory=World)
    patient_id: str | None = None
    caller_name: str | None = None  # set when someone other than the patient is acting for them
    verify_failures: int = 0
    red_flag: str | None = None
    transferred: str | None = None  # urgency, once handed to a human
    messages_left: list[dict] = field(default_factory=list)
    events: list[ToolEvent] = field(default_factory=list)
    turn: int = 0
    # Fault injection for evals: {"book_appointment": 2} makes the first two calls fail like
    # an EHR outage would. Real integrations fail; the agent has to stay honest when they do.
    faults: dict[str, int] = field(default_factory=dict)

    # ---- safety screen -------------------------------------------------------------------

    def screen_caller(self, utterance: str) -> str | None:
        hit = safety.screen(utterance)
        if hit and not self.red_flag:
            self.red_flag = hit
        return hit

    # ---- dispatch ------------------------------------------------------------------------

    def execute(self, name: str, args: dict) -> dict:
        handler = getattr(self, f"_t_{name}", None)
        try:
            if self.faults.get(name, 0) > 0:
                self.faults[name] -= 1
                raise GuardError("fault", "EHR service unavailable (HTTP 503). The request did not complete.")
            if handler is None:
                raise GuardError("validation", f"Unknown tool {name}.")
            result = handler(**(args or {}))
            self.events.append(ToolEvent(self.turn, name, args, True, result))
            return result
        except GuardError as e:
            result = {"error": str(e)}
            self.events.append(ToolEvent(self.turn, name, args, False, result, e.kind))
            return result
        except TypeError as e:  # wrong or missing arguments from the model
            result = {"error": f"Bad arguments: {e}"}
            self.events.append(ToolEvent(self.turn, name, args, False, result, "validation"))
            return result

    def _require_patient(self) -> str:
        if not self.patient_id:
            raise GuardError("identity", "Caller is not verified. Verify the patient first.")
        return self.patient_id

    def _require_no_red_flag(self) -> None:
        if self.red_flag:
            raise GuardError(
                "red_flag",
                f"Blocked: the caller mentioned possible emergency symptoms ('{self.red_flag}'). "
                "Do not book. Tell them to hang up and call 911, then transfer with urgency=emergency.",
            )

    def _open_slot(self, slot_id: str):
        slot = self.world.slots.get(slot_id)
        if slot is None:
            raise GuardError("unknown_slot", "Unknown slot_id. Only use slot ids returned by find_available_slots.")
        if slot.taken:
            raise GuardError("validation", "That slot is no longer available. Search again.")
        return slot

    def _own_appointment(self, appointment_id: str):
        pid = self._require_patient()
        appt = self.world.appointments.get(appointment_id)
        if appt is None or appt.patient_id != pid or appt.status != "booked":
            raise GuardError("ownership", "No upcoming appointment with that id for this patient.")
        return appt

    # ---- tools ---------------------------------------------------------------------------

    def _t_verify_patient(self, patient_full_name: str, patient_date_of_birth: str,
                          caller_is_patient: bool, caller_name: str | None = None) -> dict:
        if self.verify_failures >= MAX_VERIFY_FAILURES:
            raise GuardError("lockout", "Verification is locked for this call. Offer to transfer to the front desk.")
        dob = _parse_date(patient_date_of_birth)
        if dob is None:
            raise GuardError("validation", "patient_date_of_birth must be YYYY-MM-DD.")
        match = next((p for p in self.world.patients.values()
                      if p.dob == dob and _norm_name(p.full_name) == _norm_name(patient_full_name)), None)
        if match is None:
            self.verify_failures += 1
            left = MAX_VERIFY_FAILURES - self.verify_failures
            return {"verified": False, "message": f"No match for that name and date of birth. {left} attempt(s) left."}
        if not caller_is_patient:
            authorised = {" ".join(_norm_name(c)) for c in match.authorized_contacts}
            if not caller_name or " ".join(_norm_name(caller_name)) not in authorised:
                # A normal answer, not a guard hit: asking is exactly what the agent should do.
                return {"verified": False, "authorized": False,
                        "message": "The caller is not on this patient's authorised contact list. Do not share "
                                   "or change anything for this patient. The patient can call themselves, or "
                                   "add the caller as a contact."}
            self.caller_name = caller_name
        self.patient_id = match.id
        return {"verified": True, "patient_first_name": match.first_name,
                "acting_for_patient": not caller_is_patient}

    def _t_find_available_slots(self, visit_type: str, date_from: str, date_to: str,
                                provider_id: str | None = None, time_of_day: str = "any",
                                earliest_time: str | None = None) -> dict:
        start, end = _parse_date(date_from), _parse_date(date_to)
        if start is None or end is None:
            raise GuardError("validation", "Dates must be YYYY-MM-DD.")
        if visit_type not in VISIT_TYPES:
            raise GuardError("validation", f"Unknown visit_type. Use one of {list(VISIT_TYPES)}.")
        last_day = TODAY + timedelta(days=BOOKING_WINDOW_DAYS)
        start = max(start, TODAY + timedelta(days=1))
        end = min(end, last_day)
        providers = [self.world.providers[provider_id]] if provider_id else list(self.world.providers.values())
        providers = [p for p in providers if visit_type in p.visit_types]
        if not providers:
            who = self.world.providers[provider_id].name if provider_id else "No provider"
            raise GuardError("validation", f"{who} does not do {visit_type} visits.")

        not_before = None
        if earliest_time:
            try:
                h, m = map(int, earliest_time.split(":"))
                not_before = h * 60 + m
            except ValueError:
                raise GuardError("validation", "earliest_time must be HH:MM.")

        def wanted(s) -> bool:
            if s.taken or s.provider_id not in {p.id for p in providers}:
                return False
            if not_before is not None and s.start.hour * 60 + s.start.minute < not_before:
                return False
            if time_of_day == "morning" and s.start.hour >= 12:
                return False
            if time_of_day == "afternoon" and s.start.hour < 12:
                return False
            return True

        pool = sorted((s for s in self.world.slots.values() if wanted(s)), key=lambda s: s.start)
        # The first version returned the 6 earliest matches and said nothing about the rest. Ava then
        # told a caller "Monday 4 PM is the latest next week" with Tuesday 4:30 open. Say what was cut.
        matches = [s for s in pool if start <= s.start.date() <= end]
        hits = matches[:MAX_SLOTS_RETURNED]
        out = {"slots": [{"slot_id": s.id, "provider": self.world.providers[s.provider_id].name,
                          "when": spoken_datetime(s.start)} for s in hits],
               "more_available": len(matches) - len(hits)}
        if not hits:
            later = next((s for s in pool if s.start.date() > end), None)
            out["note"] = ("No openings in that range." +
                           (f" Earliest after that: {spoken_datetime(later.start)} with "
                            f"{self.world.providers[later.provider_id].name} (slot_id {later.id})."
                            if later else " Nothing in the next 30 days."))
        return out

    def _t_list_my_appointments(self) -> dict:
        pid = self._require_patient()
        appts = sorted((a for a in self.world.appointments.values()
                        if a.patient_id == pid and a.status == "booked"), key=lambda a: a.start)
        return {"appointments": [{"appointment_id": a.id, "when": spoken_datetime(a.start),
                                  "provider": self.world.providers[a.provider_id].name,
                                  "visit_type": a.visit_type} for a in appts]}

    def _check_visit_type(self, provider_id: str, visit_type: str) -> None:
        prov = self.world.providers[provider_id]
        if visit_type not in prov.visit_types:
            raise GuardError("validation", f"{prov.name} does not do {visit_type} visits.")
        if visit_type == "new_patient":
            raise GuardError("validation", "This caller is already a patient here; use another visit type.")

    def _t_book_appointment(self, slot_id: str, visit_type: str, reason: str) -> dict:
        pid = self._require_patient()
        self._require_no_red_flag()
        slot = self._open_slot(slot_id)
        self._check_visit_type(slot.provider_id, visit_type)
        if any(a.patient_id == pid and a.status == "booked" and a.start == slot.start
               for a in self.world.appointments.values()):
            raise GuardError("validation", "The patient already has an appointment at that time.")
        aid = self.world.new_appointment_id()
        self.world.appointments[aid] = Appointment(aid, pid, slot.provider_id, slot.start, visit_type, reason)
        slot.taken = True
        return {"booked": True, "appointment_id": aid, "when": spoken_datetime(slot.start),
                "provider": self.world.providers[slot.provider_id].name}

    def _t_cancel_appointment(self, appointment_id: str) -> dict:
        appt = self._own_appointment(appointment_id)
        appt.status = "cancelled"
        slot = self.world.slot_at(appt.provider_id, appt.start)
        if slot:
            slot.taken = False
        return {"cancelled": True, "when": spoken_datetime(appt.start)}

    def _t_reschedule_appointment(self, appointment_id: str, new_slot_id: str) -> dict:
        appt = self._own_appointment(appointment_id)
        self._require_no_red_flag()
        slot = self._open_slot(new_slot_id)
        if slot.provider_id != appt.provider_id:
            self._check_visit_type(slot.provider_id, appt.visit_type)
        old = self.world.slot_at(appt.provider_id, appt.start)
        if old:
            old.taken = False
        appt.provider_id, appt.start = slot.provider_id, slot.start
        slot.taken = True
        return {"rescheduled": True, "appointment_id": appt.id, "when": spoken_datetime(slot.start),
                "provider": self.world.providers[slot.provider_id].name}

    def _t_leave_message_for_staff(self, team: str, message: str) -> dict:
        self._require_patient()
        if team not in {"nurse", "billing", "front_desk"}:
            raise GuardError("validation", "team must be nurse, billing or front_desk.")
        self.messages_left.append({"team": team, "message": message, "patient_id": self.patient_id})
        return {"message_left": True, "team": team, "callback": "within one business day"}

    def _t_transfer_to_staff(self, urgency: str, reason: str) -> dict:
        if urgency not in {"routine", "urgent", "emergency"}:
            raise GuardError("validation", "urgency must be routine, urgent or emergency.")
        self.transferred = urgency
        # Say exactly what happened. When the result was just {"transferring": true}, the agent
        # (correctly) told the caller the nurse was being alerted and the judge (also correctly,
        # from what it could see) called that an unsupported claim.
        out = {"transferring": True, "to": "on-call nurse" if urgency == "emergency" else "front desk staff"}
        if urgency == "emergency":
            out["on_call_nurse_paged"] = True
        out["note"] = "Say one short closing sentence. The call is handed over after it."
        return out


def converse_tool_config() -> dict:
    return {"tools": [{"toolSpec": {"name": t["name"], "description": t["description"],
                                    "inputSchema": {"json": t["input_schema"]}}} for t in TOOL_SPECS]}
