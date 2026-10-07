# change_mind_at_readback (trial 2, policy v0): FAIL, score 65

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi there, I'd like to set up a follow-up with Dr. Raman next week, mornings are best.

**Ava [1]:** I'd be happy to help you set up a follow-up with Dr. Raman! Before I look up available times, I need to verify your identity.

Could you please give me your full name and date of birth?  _(0.857s, 1 model calls)_

**Caller [2]:** Sure, Marcus Reed, October 30th 1975.

> `verify_patient({"patient_full_name": "Marcus Reed", "patient_date_of_birth": "1975-10-30", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Marcus", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "follow_up", "provider_id": "dr_raman", "date_from": "2026-10-19", "date_to": "2026-10-23", "time_of_day": "morning"})`  
> `-> {"slots": [{"slot_id": "S-RAM-1019-1100", "provider": "Dr. Priya Raman", "when": "Monday, October 19 at 11:00 AM"}, {"slot_id": "S-RAM-1020-0900", "provider": "Dr. Priya Raman", "when": "Tuesday, October 20 at 9:00 AM"}, {"slot_id": "S-RAM-1020-0930", "provider": "Dr. Priya Raman", "when": "Tuesday, October 20 at 9:30 AM"}, {"slot_id": "S-RAM-1020-1000", "provider": "Dr. Priya Raman", "when": "Tue`  

**Ava [3]:** Great, thanks Marcus! Now let me search for morning appointments with Dr. Raman next week. Perfect! I found several morning slots with Dr. Raman next week. Here are your options:

- Monday, October 19 at 11:00 AM
- Tuesday, October 20 at 9:00 AM
- Tuesday, October 20 at 9:30 AM
- Tuesday, October 20 at 10:00 AM
- Tuesday, October 20 at 11:00 AM
- Tuesday, October 20 at 11:30 AM

There are more available too if you'd like to see other days. Which of these works best for you?  _(4.095s, 3 model calls)_

**Caller [4]:** Let's go with Tuesday the 20th at 9 AM.

**Ava [5]:** Perfect! So I'm booking you with Dr. Raman for a follow-up on Tuesday, October 20 at 9:00 AM. Does that sound right?  _(1.016s, 1 model calls)_

**Caller [6]:** Actually, sorry — I just remembered I've got a meeting that morning. Can we do Thursday instead, still in the morning?

> `find_available_slots({"date_from": "2026-10-22", "date_to": "2026-10-22", "provider_id": "dr_raman", "time_of_day": "morning", "visit_type": "follow_up"})`  
> `-> {"slots": [{"slot_id": "S-RAM-1022-0830", "provider": "Dr. Priya Raman", "when": "Thursday, October 22 at 8:30 AM"}, {"slot_id": "S-RAM-1022-0930", "provider": "Dr. Priya Raman", "when": "Thursday, October 22 at 9:30 AM"}], "more_available": 0}`  

**Ava [7]:** No problem! Let me find morning slots for you on Thursday, October 22. Great! I found two morning options on Thursday, October 22:

- 8:30 AM
- 9:30 AM

Which would work better for you?  _(2.355s, 2 model calls)_

**Caller [8]:** 9:30 works for me.

**Ava [9]:** Perfect! So I'm booking you with Dr. Raman for a follow-up on Thursday, October 22 at 9:30 AM. Is that correct?  _(0.815s, 1 model calls)_

**Caller [10]:** Yep, that's right, thanks. `[consents]`

> `book_appointment({"slot_id": "S-RAM-1022-0930", "visit_type": "follow_up", "reason": "Follow-up"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Thursday, October 22 at 9:30 AM", "provider": "Dr. Priya Raman"}`  

**Ava [11]:** Excellent! Your appointment is all set. You're booked with Dr. Raman on Thursday, October 22 at 9:30 AM. We'll see you then!  _(1.934s, 2 model calls)_

**Caller [12]:** Great, thanks a lot. Bye!

**Ava [13]:** You're welcome, Marcus! Take care!  _(0.763s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1012 dr_raman 2026-10-22T09:30 follow_up._

## Checks

- **FAIL** [major, code] `speakable` (turn 3) text-to-speech would read out '-'
- **FAIL** [minor, code] `brief_turns` (turn 3) 1 turn(s) over 60 words (longest 91)
- **FAIL** [minor, code] `options_per_turn` (turn 3) read out 5 times in one turn; callers can hold about three
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
- pass [major, code] `agent_errors` 
- pass [major, judge] `judge:caller_informed` 
- pass [minor, code] `no_question_before_tool` 
- pass [minor, code] `finished_in_budget` 
- pass [minor, judge] `judge:natural_conversation` 
