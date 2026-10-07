# reschedule_mornings_only (trial 3, policy v3): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, um, I need to move my appointment with the skin doctor.

**Ava [1]:** I'd be happy to help you reschedule your dermatology appointment. First, I need to verify who I'm speaking with. What's your full name and date of birth?  _(0.924s, 1 model calls)_

**Caller [2]:** Sure, it's Maria Lopez, March 12, 1985.

> `verify_patient({"patient_full_name": "Maria Lopez", "patient_date_of_birth": "1985-03-12", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Maria", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2001", "when": "Thursday, October 15 at 2:00 PM", "provider": "Dr. James Okafor", "visit_type": "skin_check"}]}`  

**Ava [3]:** Great, Maria. Let me pull up your appointments. I see you have a skin check with Dr. Okafor on Thursday, October 15 at 2:00 PM. When would you like to reschedule it to?  _(2.86s, 3 model calls)_

**Caller [4]:** Yeah, that's the one. Can I get something next week instead?

> `find_available_slots({"visit_type": "skin_check", "provider_id": "dr_okafor", "date_from": "2026-10-19", "date_to": "2026-10-23"})`  
> `-> {"slots": [{"slot_id": "S-OKA-1019-1130", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 11:30 AM"}, {"slot_id": "S-OKA-1019-1300", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 1:00 PM"}, {"slot_id": "S-OKA-1019-1400", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 2:00 PM"}, {"slot_id": "S-OKA-1019-1430", "provider": "Dr. James Okafor", "when": "M`  

**Ava [5]:** Let me find available times with Dr. Okafor next week. I have several options next week. How about Monday, October 19 at 11:30 AM, 1:00 PM, or 2:00 PM with Dr. Okafor?  _(2.291s, 2 model calls)_

**Caller [6]:** The 11:30 works great, I'll take that one. `[consents]`

**Ava [7]:** Just to confirm: you'd like to reschedule your skin check to Monday, October 19 at 11:30 AM with Dr. Okafor. Is that correct?  _(0.871s, 1 model calls)_

**Caller [8]:** Yes, that's correct. `[consents]`

> `reschedule_appointment({"appointment_id": "A-2001", "new_slot_id": "S-OKA-1019-1130"})`  
> `-> {"rescheduled": true, "appointment_id": "A-2001", "when": "Monday, October 19 at 11:30 AM", "provider": "Dr. James Okafor"}`  

**Ava [9]:** Perfect! Your appointment is rescheduled to Monday, October 19 at 11:30 AM with Dr. Okafor. Is there anything else I can help with?  _(1.95s, 2 model calls)_

**Caller [10]:** No, that's everything. Thanks so much, bye!

**Ava [11]:** You're welcome, Maria. Have a great day!  _(0.755s, 1 model calls)_

_Call ended: caller_done. Clinic system change: moved A-2001 to dr_okafor 2026-10-19T11:30._

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
