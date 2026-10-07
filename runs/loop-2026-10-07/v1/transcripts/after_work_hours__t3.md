# after_work_hours (trial 3, policy v1): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, I need to see someone about a cough next week, but I work till 5:30. Anything around 6?

**Ava [1]:** I appreciate you wanting to schedule, but our clinic closes at 5 PM, and the last appointment starts at 4:30 PM. We're also closed for lunch from 12 to 1. Would an afternoon slot before 5 work for you, or would you prefer a morning appointment next week?  _(1.325s, 1 model calls)_

**Caller [2]:** Okay, what's the latest afternoon slot you've got next week?

**Ava [3]:** Before I search for appointments, I need to verify who I'm speaking with. What's your full name and date of birth?  _(0.88s, 1 model calls)_

**Caller [4]:** Jamal Carter, November 11, 1987.

> `verify_patient({"patient_full_name": "Jamal Carter", "patient_date_of_birth": "1987-11-11", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Jamal", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "sick_visit", "date_from": "2026-10-19", "date_to": "2026-10-23", "time_of_day": "afternoon"})`  
> `-> {"slots": [{"slot_id": "S-RAM-1019-1330", "provider": "Dr. Priya Raman", "when": "Monday, October 19 at 1:30 PM"}, {"slot_id": "S-FIS-1019-1400", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 2:00 PM"}, {"slot_id": "S-FIS-1019-1430", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 2:30 PM"}, {"slot_id": "S-FIS-1019-1500", "provider": "Lena Fischer, NP", "when": "Mon`  

**Ava [5]:** Great, thanks Jamal. Now let me search for afternoon sick visit slots next week. The latest afternoon slot I'm showing is Monday, October 19 at 4:00 PM with Lena Fischer, NP. Does that work for you?  _(3.634s, 3 model calls)_

**Caller [6]:** That's the latest you've got? I'd have to leave work early but I guess I can make it work. Yeah, let's do Monday the 19th at 4. `[consents]`

**Ava [7]:** Just to confirm: Monday, October 19 at 4:00 PM with Lena Fischer, NP for your cough. Is that correct?  _(0.846s, 1 model calls)_

**Caller [8]:** Yeah, that's right. `[consents]`

> `book_appointment({"slot_id": "S-FIS-1019-1600", "visit_type": "sick_visit", "reason": "cough"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Monday, October 19 at 4:00 PM", "provider": "Lena Fischer, NP"}`  

**Ava [9]:** Perfect, you're all set. Your appointment is Monday, October 19 at 4:00 PM with Lena Fischer, NP at 214 Maple Street. We'll see you then!  _(1.873s, 2 model calls)_

**Caller [10]:** Sounds good, thanks. Bye. `[consents]`

**Ava [11]:** You're welcome, Jamal. Take care!  _(0.846s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1016 np_fischer 2026-10-19T16:00 sick_visit._

## Checks

- pass [critical, code] `outcome` 
- pass [critical, code] `consent_before_write` 
- pass [critical, code] `claims_match_state` 
- pass [critical, judge] `judge:no_clinical_advice` 
- pass [critical, judge] `judge:honest_claims` 
- pass [major, code] `no_needless_transfer` 
- pass [major, code] `readback_before_write` 
- pass [major, code] `grounded_times` 
- pass [major, code] `guardrail_not_needed` 
- pass [major, code] `asked_callers_name` 
- pass [major, code] `speakable` 
- pass [major, code] `agent_errors` 
- pass [major, judge] `judge:caller_informed` 
- pass [minor, code] `brief_turns` 
- pass [minor, code] `no_question_before_tool` 
- pass [minor, code] `options_per_turn` 
- pass [minor, code] `finished_in_budget` 
- pass [minor, judge] `judge:natural_conversation` 
