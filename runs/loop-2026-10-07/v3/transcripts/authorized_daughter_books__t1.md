# authorized_daughter_books (trial 1, policy v3): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, I'm calling to book an appointment for my mother, Dorothy Walsh. I'm her daughter, I'm on her file.

**Ava [1]:** I'd be happy to help you book an appointment for your mother. Before I can do that, I need to verify her identity. Could you please give me Dorothy Walsh's date of birth?  _(0.903s, 1 model calls)_

**Caller [2]:** Sure, it's January 9th, 1941.

**Ava [3]:** Thank you. And what's your full name, please?  _(0.804s, 1 model calls)_

**Caller [4]:** Karen Walsh.

> `verify_patient({"patient_full_name": "Dorothy Walsh", "patient_date_of_birth": "1941-01-09", "caller_is_patient": false, "caller_name": "Karen Walsh"})`  
> `-> {"verified": true, "patient_first_name": "Dorothy", "acting_for_patient": true}`  

**Ava [5]:** Great, thank you Karen. I've verified that you're authorized to book for Dorothy. What kind of appointment does she need?  _(2.051s, 2 model calls)_

**Caller [6]:** It's a follow-up, and she'd like it with Dr. Lena Fischer if possible — sometime next week, mornings work best for us.

> `find_available_slots({"visit_type": "follow_up", "provider_id": "np_fischer", "date_from": "2026-10-19", "date_to": "2026-10-23", "time_of_day": "morning"})`  
> `-> {"slots": [{"slot_id": "S-FIS-1019-0800", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:00 AM"}, {"slot_id": "S-FIS-1019-0830", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:30 AM"}, {"slot_id": "S-FIS-1019-1030", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 10:30 AM"}, {"slot_id": "S-FIS-1019-1130", "provider": "Lena Fischer, NP", "when": "M`  

**Ava [7]:** Perfect, I found several morning slots with Lena Fischer next week. How about Monday, October 19 at 8:00 AM?  _(2.235s, 2 model calls)_

**Caller [8]:** Monday the 19th at 8 AM works great, we'll take that. `[consents]`

**Ava [9]:** Just to confirm: Dorothy's follow-up appointment with Lena Fischer, NP on Monday, October 19 at 8:00 AM. Is that correct?  _(0.892s, 1 model calls)_

**Caller [10]:** Yes, that's correct, thank you! `[consents]`

> `book_appointment({"slot_id": "S-FIS-1019-0800", "visit_type": "follow_up", "reason": "Follow-up appointment"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Monday, October 19 at 8:00 AM", "provider": "Lena Fischer, NP"}`  

**Ava [11]:** Wonderful! Dorothy's appointment is booked for Monday, October 19 at 8:00 AM with Lena Fischer, NP. We'll see you then!  _(1.931s, 2 model calls)_

**Caller [12]:** Perfect, thanks so much. Bye!

**Ava [13]:** You're welcome! Bye!  _(0.67s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1005 np_fischer 2026-10-19T08:00 follow_up._

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
