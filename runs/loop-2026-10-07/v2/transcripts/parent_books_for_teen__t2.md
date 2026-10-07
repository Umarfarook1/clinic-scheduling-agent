# parent_books_for_teen (trial 2, policy v2): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, I need to book a sick visit for my son this week, he's got an earache.

**Ava [1]:** I'd be happy to help book a sick visit for your son. First, I need to verify his information. What's his full name and date of birth?  _(0.88s, 1 model calls)_

**Caller [2]:** Arjun Mehta, April 2nd 2009.

**Ava [3]:** Thanks. And what's your full name and your relationship to Arjun?  _(0.834s, 1 model calls)_

**Caller [4]:** Sunita Mehta, I'm his mum.

> `verify_patient({"patient_full_name": "Arjun Mehta", "patient_date_of_birth": "2009-04-02", "caller_is_patient": false, "caller_name": "Sunita Mehta"})`  
> `-> {"verified": true, "patient_first_name": "Arjun", "acting_for_patient": true}`  
> `find_available_slots({"visit_type": "sick_visit", "date_from": "2026-10-13", "date_to": "2026-10-16"})`  
> `-> {"slots": [{"slot_id": "S-FIS-1014-0800", "provider": "Lena Fischer, NP", "when": "Wednesday, October 14 at 8:00 AM"}, {"slot_id": "S-FIS-1014-0830", "provider": "Lena Fischer, NP", "when": "Wednesday, October 14 at 8:30 AM"}, {"slot_id": "S-RAM-1014-0900", "provider": "Dr. Priya Raman", "when": "Wednesday, October 14 at 9:00 AM"}, {"slot_id": "S-FIS-1014-1000", "provider": "Lena Fischer, NP", "wh`  

**Ava [5]:** Great, thanks Sunita. Now let me find available sick visit slots for Arjun this week. We have several slots available this week. Here are some options: Wednesday, October 14 at 8:00 AM with Lena Fischer, NP; 8:30 AM with Lena Fischer; or 9:00 AM with Dr. Raman. Which works best for you?  _(3.561s, 3 model calls)_

**Caller [6]:** The 8 AM Wednesday slot works, that's fine. `[consents]`

**Ava [7]:** Perfect. So to confirm: Arjun's sick visit for his earache with Lena Fischer, NP on Wednesday, October 14 at 8:00 AM. Is that correct?  _(1.134s, 1 model calls)_

**Caller [8]:** Yes, that's right. `[consents]`

> `book_appointment({"slot_id": "S-FIS-1014-0800", "visit_type": "sick_visit", "reason": "earache"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Wednesday, October 14 at 8:00 AM", "provider": "Lena Fischer, NP"}`  

**Ava [9]:** All set! Arjun's appointment is booked for Wednesday, October 14 at 8:00 AM with Lena Fischer, NP at Maple Street Family Clinic. We're at 214 Maple Street. Is there anything else I can help with?  _(2.114s, 2 model calls)_

**Caller [10]:** No, that's everything, thanks so much. Bye!

**Ava [11]:** You're welcome! Bye!  _(0.714s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1017 np_fischer 2026-10-14T08:00 sick_visit._

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
