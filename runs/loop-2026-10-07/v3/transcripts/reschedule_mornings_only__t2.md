# reschedule_mornings_only (trial 2, policy v3): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, um, I need to move my appointment with the skin doctor.

**Ava [1]:** I'd be happy to help you reschedule your dermatology appointment. To get started, I need to verify your identity. Can you please give me your full name and date of birth?  _(1.0s, 1 model calls)_

**Caller [2]:** Sure, it's Maria Lopez, March 12, 1985.

> `verify_patient({"patient_full_name": "Maria Lopez", "patient_date_of_birth": "1985-03-12", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Maria", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2001", "when": "Thursday, October 15 at 2:00 PM", "provider": "Dr. James Okafor", "visit_type": "skin_check"}]}`  

**Ava [3]:** Great, Maria. Now let me pull up your appointments to see which skin check appointment you'd like to move. You have a skin check with Dr. Okafor on Thursday, October 15 at 2:00 PM. When would you like to reschedule it to?  _(3.168s, 3 model calls)_

**Caller [4]:** Yeah, that's the one. Can I get something next week?

**Ava [5]:** Sure. What day next week works best for you, and do you prefer morning or afternoon?  _(0.909s, 1 model calls)_

**Caller [6]:** Morning works best for me — any day next week is fine.

> `find_available_slots({"visit_type": "skin_check", "provider_id": "dr_okafor", "date_from": "2026-10-19", "date_to": "2026-10-23", "time_of_day": "morning"})`  
> `-> {"slots": [{"slot_id": "S-OKA-1019-1130", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 11:30 AM"}, {"slot_id": "S-OKA-1020-1000", "provider": "Dr. James Okafor", "when": "Tuesday, October 20 at 10:00 AM"}, {"slot_id": "S-OKA-1020-1030", "provider": "Dr. James Okafor", "when": "Tuesday, October 20 at 10:30 AM"}, {"slot_id": "S-OKA-1020-1130", "provider": "Dr. James Okafor", "when"`  

**Ava [7]:** I have several morning options next week. How about Wednesday, October 21 at 8:30 AM with Dr. Okafor?  _(2.18s, 2 model calls)_

**Caller [8]:** Yeah, that works for me! `[consents]`

**Ava [9]:** Just to confirm: you'd like to reschedule your skin check to Wednesday, October 21 at 8:30 AM with Dr. Okafor. Is that correct?  _(0.901s, 1 model calls)_

**Caller [10]:** Yes, that's correct. `[consents]`

> `reschedule_appointment({"appointment_id": "A-2001", "new_slot_id": "S-OKA-1021-0830"})`  
> `-> {"rescheduled": true, "appointment_id": "A-2001", "when": "Wednesday, October 21 at 8:30 AM", "provider": "Dr. James Okafor"}`  

**Ava [11]:** Perfect! Your appointment is rescheduled to Wednesday, October 21 at 8:30 AM with Dr. Okafor. Is there anything else I can help with?  _(1.888s, 2 model calls)_

**Caller [12]:** Nope, that's all. Thanks so much, bye!

**Ava [13]:** You're welcome, Maria. Have a great day!  _(0.738s, 1 model calls)_

_Call ended: caller_done. Clinic system change: moved A-2001 to dr_okafor 2026-10-21T08:30._

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
