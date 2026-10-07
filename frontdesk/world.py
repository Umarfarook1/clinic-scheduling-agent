"""The clinic the agent works in: providers, patients, open slots, booked appointments.

Everything is in memory and deterministic. Every conversation gets its own fresh copy of the
world, so the eval can diff the end state against the start state and know exactly what the
agent changed, instead of trusting what the agent said it changed.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

# Frozen "today" (a Tuesday). "Next Friday" has to mean the same day in every run, or the
# scores move for reasons that have nothing to do with the agent.
TODAY = date(2026, 10, 13)
NOW = datetime(2026, 10, 13, 9, 0)
BOOKING_WINDOW_DAYS = 30

CLINIC_NAME = "Maple Street Family Clinic"
CLINIC_FACTS = (
    "Maple Street Family Clinic, 214 Maple Street. Open Monday to Friday, 8 AM to 5 PM, "
    "closed for lunch 12 to 1, closed on weekends. Appointments are 30 minutes. "
    "The last appointment of the day starts at 4:30 PM."
)

VISIT_TYPES = {
    "checkup": "annual checkup or physical",
    "follow_up": "follow-up on an existing issue",
    "sick_visit": "new, non-emergency illness",
    "skin_check": "dermatology visit (skin, moles, rashes)",
    "new_patient": "first visit for someone not yet a patient here",
}


@dataclass
class Provider:
    id: str
    name: str
    specialty: str
    visit_types: list[str]
    accepts_new_patients: bool


@dataclass
class Patient:
    id: str
    first_name: str
    last_name: str
    dob: date
    phone: str
    # People the patient has authorised to speak for them (HIPAA release on file).
    authorized_contacts: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Slot:
    id: str
    provider_id: str
    start: datetime
    taken: bool = False


@dataclass
class Appointment:
    id: str
    patient_id: str
    provider_id: str
    start: datetime
    visit_type: str
    reason: str
    status: str = "booked"  # booked | cancelled


PROVIDERS = [
    Provider("dr_raman", "Dr. Priya Raman", "family medicine", ["checkup", "follow_up", "sick_visit"], False),
    Provider("np_fischer", "Lena Fischer, NP", "family medicine",
             ["checkup", "follow_up", "sick_visit", "new_patient"], True),
    Provider("dr_okafor", "Dr. James Okafor", "dermatology", ["skin_check", "follow_up"], True),
]

PATIENTS = [
    Patient("PT-1001", "Maria", "Lopez", date(1985, 3, 12), "555-0142"),
    Patient("PT-1002", "Robert", "Chen", date(1958, 7, 30), "555-0177"),
    Patient("PT-1003", "Linda", "Chen", date(1960, 11, 2), "555-0177"),
    Patient("PT-1004", "Aisha", "Bello", date(1992, 5, 21), "555-0110"),
    Patient("PT-1005", "Dorothy", "Walsh", date(1941, 1, 9), "555-0123", authorized_contacts=["Karen Walsh"]),
    Patient("PT-1006", "Daniel", "Kim", date(1979, 9, 14), "555-0190"),
    Patient("PT-1007", "Samuel", "Ortiz", date(1988, 12, 3), "555-0161"),
    Patient("PT-1008", "Grace", "Thompson", date(1970, 4, 25), "555-0135"),
    Patient("PT-1009", "Ben", "Novak", date(1996, 8, 17), "555-0188"),
    Patient("PT-1010", "Tom", "Becker", date(1983, 6, 8), "555-0152"),
    Patient("PT-1011", "Hannah", "Schultz", date(1999, 2, 14), "555-0119"),
    Patient("PT-1012", "Marcus", "Reed", date(1975, 10, 30), "555-0166"),
    Patient("PT-1013", "Olivia", "Park", date(2001, 7, 7), "555-0104"),
    Patient("PT-1014", "Victor", "Nunez", date(1966, 3, 19), "555-0181"),
    Patient("PT-1015", "Emma", "Davis", date(1990, 9, 9), "555-0129"),
    Patient("PT-1016", "Jamal", "Carter", date(1987, 11, 11), "555-0148"),
    Patient("PT-1017", "Arjun", "Mehta", date(2009, 4, 2), "555-0172", authorized_contacts=["Sunita Mehta"]),
]

# Appointments that exist before any call. Ids are referenced by scenario expectations.
SEED_APPOINTMENTS = [
    ("A-2001", "PT-1001", "dr_okafor", datetime(2026, 10, 15, 14, 0), "skin_check", "mole check"),
    ("A-2002", "PT-1002", "dr_raman", datetime(2026, 10, 16, 10, 30), "follow_up", "blood pressure follow-up"),
    ("A-2003", "PT-1007", "dr_raman", datetime(2026, 10, 15, 8, 30), "follow_up", "blood work review"),
    ("A-2004", "PT-1005", "np_fischer", datetime(2026, 10, 27, 11, 0), "checkup", "annual checkup"),
    ("A-2005", "PT-1008", "np_fischer", datetime(2026, 10, 14, 15, 30), "sick_visit", "sinus infection"),
    ("A-2006", "PT-1010", "dr_raman", datetime(2026, 10, 22, 9, 0), "follow_up", "back pain follow-up"),
    ("A-2007", "PT-1015", "np_fischer", datetime(2026, 10, 20, 13, 30), "sick_visit", "lower back pain"),
]

DAY_TIMES = [time(h, m) for h in (8, 9, 10, 11, 13, 14, 15, 16) for m in (0, 30)]


def _build_slots() -> list[Slot]:
    """About 60% of slots are taken, from a fixed seed, plus a few hand-set facts the
    scenarios lean on (dermatology is full this week, Saturday does not exist, and so on)."""
    rng = random.Random(7)
    slots: list[Slot] = []
    day = TODAY + timedelta(days=1)
    end = TODAY + timedelta(days=BOOKING_WINDOW_DAYS)
    while day <= end:
        if day.weekday() < 5:
            for p in PROVIDERS:
                for t in DAY_TIMES:
                    start = datetime.combine(day, t)
                    code = p.id.split("_")[1][:3].upper()
                    slots.append(Slot(f"S-{code}-{start:%m%d-%H%M}", p.id, start, taken=rng.random() < 0.6))
        day += timedelta(days=1)

    by_key = {(s.provider_id, s.start): s for s in slots}

    def force(provider_id: str, d: date, hhmm: str, taken: bool) -> None:
        h, m = map(int, hhmm.split(":"))
        by_key[(provider_id, datetime.combine(d, time(h, m)))].taken = taken

    # Dermatology is fully booked for the rest of this week.
    for s in slots:
        if s.provider_id == "dr_okafor" and s.start.date() <= date(2026, 10, 16):
            s.taken = True
    # ...and has a few mornings and afternoons next week.
    for d, hhmm in [(date(2026, 10, 19), "15:00"), (date(2026, 10, 20), "13:30"),
                    (date(2026, 10, 21), "09:00"), (date(2026, 10, 21), "10:30"),
                    (date(2026, 10, 22), "08:30"), (date(2026, 10, 22), "14:00")]:
        force("dr_okafor", d, hhmm, False)
    # Dr. Raman has a Tuesday and a Thursday morning next week (change-of-mind scenario).
    force("dr_raman", date(2026, 10, 20), "10:00", False)
    force("dr_raman", date(2026, 10, 22), "09:30", False)
    # Late-afternoon openings exist next week (the "after work" caller).
    force("np_fischer", date(2026, 10, 20), "16:30", False)
    force("dr_raman", date(2026, 10, 21), "16:00", False)
    # Seed appointments occupy their slots.
    for _, _, prov, start, _, _ in SEED_APPOINTMENTS:
        if (prov, start) in by_key:
            by_key[(prov, start)].taken = True
    return slots


class World:
    def __init__(self) -> None:
        self.providers = {p.id: p for p in PROVIDERS}
        self.patients = {p.id: p for p in PATIENTS}
        self.slots = {s.id: s for s in _build_slots()}
        self.appointments = {
            aid: Appointment(aid, pid, prov, start, vt, reason)
            for aid, pid, prov, start, vt, reason in SEED_APPOINTMENTS
        }
        self._next_appt = 3001

    def new_appointment_id(self) -> str:
        aid = f"A-{self._next_appt}"
        self._next_appt += 1
        return aid

    def slot_at(self, provider_id: str, start: datetime) -> Slot | None:
        for s in self.slots.values():
            if s.provider_id == provider_id and s.start == start:
                return s
        return None

    def snapshot(self) -> dict:
        """Plain-data view of everything a call can change, for before/after diffs."""
        return {
            "appointments": {
                a.id: {"patient_id": a.patient_id, "provider_id": a.provider_id,
                       "start": a.start.isoformat(timespec="minutes"), "visit_type": a.visit_type,
                       "status": a.status}
                for a in self.appointments.values()
            }
        }


def spoken_datetime(dt: datetime) -> str:
    """'Wednesday, October 21 at 9:30 AM'. What the tools hand back, so the agent never has
    to turn an ISO string into speech itself (a common place for weekday mistakes)."""
    hour = dt.strftime("%I").lstrip("0")
    return f"{dt:%A, %B} {dt.day} at {hour}:{dt:%M} {dt:%p}"
