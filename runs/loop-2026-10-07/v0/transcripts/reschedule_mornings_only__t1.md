# reschedule_mornings_only (trial 1, policy v0): FAIL, score 70

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, um, I need to move my appointment with the skin doctor.

**Ava [1]:** I'd be happy to help you reschedule your dermatology appointment! Let me first confirm who I'm speaking with.

Can you please give me your full name and date of birth?  _(0.935s, 1 model calls)_

**Caller [2]:** Sure, it's Maria Lopez, date of birth March 12, 1985.

> `verify_patient({"patient_full_name": "Maria Lopez", "patient_date_of_birth": "1985-03-12", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Maria", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2001", "when": "Thursday, October 15 at 2:00 PM", "provider": "Dr. James Okafor", "visit_type": "skin_check"}]}`  

**Ava [3]:** Great, Maria! Now let me pull up your appointments to see which skin check appointment you'd like to move. Perfect! I see you have a skin check appointment with Dr. Okafor on Thursday, October 15 at 2:00 PM. When would you like to reschedule it to?  _(3.147s, 3 model calls)_

**Caller [4]:** Yeah, that's the one. I need to move it to sometime next week.

**Ava [5]:** Got it! Next week works. Do you have a preference for a specific day, or a particular time of day like morning or afternoon?  _(0.936s, 1 model calls)_

**Caller [6]:** Mornings only for me, any day next week is fine.

> `find_available_slots({"visit_type": "skin_check", "provider_id": "dr_okafor", "date_from": "2026-10-19", "date_to": "2026-10-23", "time_of_day": "morning"})`  
> `-> {"slots": [{"slot_id": "S-OKA-1019-1130", "provider": "Dr. James Okafor", "when": "Monday, October 19 at 11:30 AM"}, {"slot_id": "S-OKA-1020-1000", "provider": "Dr. James Okafor", "when": "Tuesday, October 20 at 10:00 AM"}, {"slot_id": "S-OKA-1020-1030", "provider": "Dr. James Okafor", "when": "Tuesday, October 20 at 10:30 AM"}, {"slot_id": "S-OKA-1020-1130", "provider": "Dr. James Okafor", "when"`  

**Ava [7]:** Great! I have several morning options for you next week with Dr. Okafor:

- Monday, October 19 at 11:30 AM
- Tuesday, October 20 at 10:00 AM, 10:30 AM, or 11:30 AM
- Wednesday, October 21 at 8:30 AM or 9:00 AM

Which of these works best for you?  _(2.547s, 2 model calls)_

**Caller [8]:** Monday the 19th at 11:30 works great, I'll take that one. `[consents]`

**Ava [9]:** Perfect! Let me confirm: I'm going to move your skin check appointment with Dr. Okafor from Thursday, October 15 at 2:00 PM to Monday, October 19 at 11:30 AM. Does that sound right?  _(1.173s, 1 model calls)_

**Caller [10]:** Yep, that's perfect, thank you! `[consents]`

> `reschedule_appointment({"appointment_id": "A-2001", "new_slot_id": "S-OKA-1019-1130"})`  
> `-> {"rescheduled": true, "appointment_id": "A-2001", "when": "Monday, October 19 at 11:30 AM", "provider": "Dr. James Okafor"}`  

**Ava [11]:** Excellent! Your appointment is all set for Monday, October 19 at 11:30 AM with Dr. Okafor. Thanks for calling Maple Street Family Clinic!  _(1.986s, 2 model calls)_

**Caller [12]:** Great, thanks so much. Bye! `[consents]`

**Ava [13]:** You're welcome! Bye, Maria!  _(0.741s, 1 model calls)_

_Call ended: caller_done. Clinic system change: moved A-2001 to dr_okafor 2026-10-19T11:30._

## Checks

- **FAIL** [major, code] `speakable` (turn 7) text-to-speech would read out '-'
- **FAIL** [minor, code] `options_per_turn` (turn 7) read out 5 times in one turn; callers can hold about three
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
