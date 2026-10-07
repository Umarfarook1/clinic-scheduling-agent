# reschedule_mornings_only (trial 3, policy v0): FAIL, score 70

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, um, I need to move my appointment with the skin doctor.

**Ava [1]:** I'd be happy to help you reschedule your dermatology appointment! Let me first confirm who I'm speaking with.

Can you please give me your full name and date of birth?  _(0.943s, 1 model calls)_

**Caller [2]:** Sure, it's Maria Lopez, date of birth March 12, 1985.

> `verify_patient({"patient_full_name": "Maria Lopez", "patient_date_of_birth": "1985-03-12", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Maria", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2001", "when": "Thursday, October 15 at 2:00 PM", "provider": "Dr. James Okafor", "visit_type": "skin_check"}]}`  

**Ava [3]:** Great, Maria! Now let me pull up your appointments. Perfect! I see you have a skin check appointment with Dr. Okafor on Thursday, October 15 at 2:00 PM. When would you like to reschedule it to?  _(2.948s, 3 model calls)_

**Caller [4]:** I need to move it to sometime next week, if that works.

> `find_available_slots({"visit_type": "skin_check", "provider_id": "dr_okafor", "date_from": "2026-10-19", "date_to": "2026-10-23"})`  
> `-> {"slots": [{"slot_id": "S-OKA-1019-1130", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 11:30 AM"}, {"slot_id": "S-OKA-1019-1300", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 1:00 PM"}, {"slot_id": "S-OKA-1019-1400", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 2:00 PM"}, {"slot_id": "S-OKA-1019-1430", "provider": "Dr. James Okafor", "when": "M`  

**Ava [5]:** Let me check what's available with Dr. Okafor next week. Great! Dr. Okafor has several openings next week. Here are some options:

**Monday, October 19:** 11:30 AM, 1:00 PM, 2:00 PM, 2:30 PM, or 3:00 PM

**Tuesday, October 20:** 10:00 AM

There are more times available later in the week too. What works best for you?  _(2.49s, 2 model calls)_

**Caller [6]:** Monday at 11:30 works great, I'll take that one. `[consents]`

**Ava [7]:** Perfect! Let me confirm the details:

**Moving your appointment to:**
- Monday, October 19 at 11:30 AM
- With Dr. James Okafor
- Skin check visit

Does that all look good?  _(1.076s, 1 model calls)_

**Caller [8]:** Yes, that's perfect, thanks so much! `[consents]`

> `reschedule_appointment({"appointment_id": "A-2001", "new_slot_id": "S-OKA-1019-1130"})`  
> `-> {"rescheduled": true, "appointment_id": "A-2001", "when": "Monday, October 19 at 11:30 AM", "provider": "Dr. James Okafor"}`  

**Ava [9]:** Excellent! Your appointment is all set for Monday, October 19 at 11:30 AM with Dr. Okafor. Thanks for calling Maple Street Family Clinic!  _(1.983s, 2 model calls)_

**Caller [10]:** Great, thanks! Bye!

**Ava [11]:** You're welcome! Bye, Maria!  _(0.719s, 1 model calls)_

_Call ended: caller_done. Clinic system change: moved A-2001 to dr_okafor 2026-10-19T11:30._

## Checks

- **FAIL** [major, code] `speakable` (turn 5) text-to-speech would read out '**'
- **FAIL** [minor, code] `options_per_turn` (turn 5) read out 6 times in one turn; callers can hold about three
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
- pass [minor, code] `brief_turns` 
- pass [minor, code] `no_question_before_tool` 
- pass [minor, code] `finished_in_budget` 
- pass [minor, judge] `judge:natural_conversation` 
