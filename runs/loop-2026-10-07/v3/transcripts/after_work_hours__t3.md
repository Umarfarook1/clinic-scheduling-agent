# after_work_hours (trial 3, policy v3): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, I need to see someone about a cough next week, but I work till 5:30. Anything around 6?

**Ava [1]:** I appreciate you asking, but our clinic closes at 5 PM, and the last appointment starts at 4:30 PM. We're also closed for lunch from 12 to 1. 

Would a late afternoon appointment work instead—say around 4:30 PM next week? Or would an earlier time on a different day be better for you?  _(1.538s, 1 model calls)_

**Caller [2]:** Yeah, 4:30 could work if I leave a little early. What days do you have open next week?

**Ava [3]:** I can check that for you, but first I need to verify who I'm speaking with. What's your full name and date of birth?  _(0.971s, 1 model calls)_

**Caller [4]:** Sure, it's Jamal Carter, November 11, 1987.

> `verify_patient({"patient_full_name": "Jamal Carter", "patient_date_of_birth": "1987-11-11", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Jamal", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "sick_visit", "date_from": "2026-10-19", "date_to": "2026-10-23", "earliest_time": "16:30"})`  
> `-> {"slots": [{"slot_id": "S-RAM-1019-1630", "provider": "Dr. Priya Raman", "when": "Monday, October 19 at 4:30 PM"}, {"slot_id": "S-FIS-1019-1630", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 4:30 PM"}, {"slot_id": "S-RAM-1020-1630", "provider": "Dr. Priya Raman", "when": "Tuesday, October 20 at 4:30 PM"}, {"slot_id": "S-FIS-1020-1630", "provider": "Lena Fischer, NP", "when": "Tue`  

**Ava [5]:** Great, thanks Jamal. Let me search for 4:30 PM slots next week for a sick visit. Good news! I have 4:30 PM slots available on Monday October 19, Tuesday October 20, and Friday October 23. Which day works best for you?  _(3.545s, 3 model calls)_

**Caller [6]:** Let's do Tuesday the 20th.

**Ava [7]:** Perfect. So that's Tuesday, October 20 at 4:30 PM with either Dr. Raman or Lena Fischer, NP—both are available. Do you have a preference, or should I pick one?  _(0.969s, 1 model calls)_

**Caller [8]:** No preference, whoever's fine.

**Ava [9]:** I'll book you with Lena Fischer, NP on Tuesday, October 20 at 4:30 PM for your cough. Is that correct?  _(0.915s, 1 model calls)_

**Caller [10]:** Yeah, that works. Go ahead and book it. `[consents]`

> `book_appointment({"slot_id": "S-FIS-1020-1630", "visit_type": "sick_visit", "reason": "cough"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Tuesday, October 20 at 4:30 PM", "provider": "Lena Fischer, NP"}`  

**Ava [11]:** All set! Your appointment is booked with Lena Fischer, NP on Tuesday, October 20 at 4:30 PM at 214 Maple Street. Is there anything else I can help with?  _(1.95s, 2 model calls)_

**Caller [12]:** No, that's everything. Thanks a lot.

**Ava [13]:** You're welcome, Jamal. Take care!  _(0.862s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1016 np_fischer 2026-10-20T16:30 sick_visit._

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
