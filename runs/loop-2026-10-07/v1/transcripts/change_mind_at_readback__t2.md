# change_mind_at_readback (trial 2, policy v1): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi there, I'd like to set up a follow-up with Dr. Raman next week, mornings are best.

**Ava [1]:** I'd be happy to help you set up a follow-up with Dr. Raman next week in the morning. First, I need to verify who I'm speaking with. What's your full name and date of birth?  _(0.907s, 1 model calls)_

**Caller [2]:** Sure, it's Marcus Reed, October 30th, 1975.

> `verify_patient({"patient_full_name": "Marcus Reed", "patient_date_of_birth": "1975-10-30", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Marcus", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "follow_up", "provider_id": "dr_raman", "date_from": "2026-10-19", "date_to": "2026-10-23", "time_of_day": "morning"})`  
> `-> {"slots": [{"slot_id": "S-RAM-1019-1100", "provider": "Dr. Priya Raman", "when": "Monday, October 19 at 11:00 AM"}, {"slot_id": "S-RAM-1020-0900", "provider": "Dr. Priya Raman", "when": "Tuesday, October 20 at 9:00 AM"}, {"slot_id": "S-RAM-1020-0930", "provider": "Dr. Priya Raman", "when": "Tuesday, October 20 at 9:30 AM"}, {"slot_id": "S-RAM-1020-1000", "provider": "Dr. Priya Raman", "when": "Tue`  

**Ava [3]:** Great, Marcus. Now let me find some morning slots with Dr. Raman for next week. I found several morning options with Dr. Raman next week. How about Tuesday, October 20 at 9:00 AM, 9:30 AM, or 10:00 AM?  _(3.539s, 3 model calls)_

**Caller [4]:** Tuesday the 20th at 9 AM works for me. `[consents]`

**Ava [5]:** Perfect. So to confirm, I'm booking you with Dr. Raman on Tuesday, October 20 at 9:00 AM for a follow-up. Is that correct?  _(1.008s, 1 model calls)_

**Caller [6]:** Actually, sorry — I just remembered I've got a meeting that morning. Could we do Thursday instead, still in the morning?

> `find_available_slots({"date_from": "2026-10-22", "date_to": "2026-10-22", "provider_id": "dr_raman", "time_of_day": "morning", "visit_type": "follow_up"})`  
> `-> {"slots": [{"slot_id": "S-RAM-1022-0830", "provider": "Dr. Priya Raman", "when": "Thursday, October 22 at 8:30 AM"}, {"slot_id": "S-RAM-1022-0930", "provider": "Dr. Priya Raman", "when": "Thursday, October 22 at 9:30 AM"}], "more_available": 0}`  

**Ava [7]:** No problem. Let me find morning slots with Dr. Raman on Thursday, October 22. I have two morning options on Thursday, October 22: 8:30 AM or 9:30 AM. Which works better for you?  _(2.331s, 2 model calls)_

**Caller [8]:** 9:30 works great, thanks.

**Ava [9]:** Perfect. So to confirm, I'm booking you with Dr. Raman on Thursday, October 22 at 9:30 AM for a follow-up. Does that work?  _(0.825s, 1 model calls)_

**Caller [10]:** Yes, that's perfect, thanks. `[consents]`

> `book_appointment({"slot_id": "S-RAM-1022-0930", "visit_type": "follow_up", "reason": "follow-up"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Thursday, October 22 at 9:30 AM", "provider": "Dr. Priya Raman"}`  

**Ava [11]:** Great! Your appointment is all set with Dr. Raman on Thursday, October 22 at 9:30 AM. Is there anything else I can help you with?  _(1.902s, 2 model calls)_

**Caller [12]:** Nope, that's everything. Thanks a lot, bye!

**Ava [13]:** You're welcome, Marcus. Have a great day!  _(0.79s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1012 dr_raman 2026-10-22T09:30 follow_up._

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
