# barge_in_readback (trial 2, policy v3): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** hi yeah I need a checkup next week sometime  
_(speech-to-text heard: "hi yeah i need a checkup next week sometime")_

**Ava [1]:** I'd be happy to help you book a checkup for next week. First, I need to verify who I'm speaking with. What's your full name and date of birth?  _(0.858s, 1 model calls)_

**Caller [2]:** Yeah it's Olivia Park, birthday's July 7th 2001  
_(speech-to-text heard: "yeah it's olivia park birthday's july 7th 2001")_

**Ava [3]:** Thanks Olivia. Just to confirm, your date of birth is July 7th, 2001, and you're calling for yourself, correct?  _(0.955s, 1 model calls)_

**Caller [4]:** Yep that's me.  
_(speech-to-text heard: "yep that's me")_

> `verify_patient({"patient_full_name": "Olivia Park", "patient_date_of_birth": "2001-07-07", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Olivia", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "checkup", "date_from": "2026-10-19", "date_to": "2026-10-23"})`  
> `-> {"slots": [{"slot_id": "S-FIS-1019-0800", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:00 AM"}, {"slot_id": "S-FIS-1019-0830", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:30 AM"}, {"slot_id": "S-FIS-1019-1030", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 10:30 AM"}, {"slot_id": "S-RAM-1019-1100", "provider": "Dr. Priya Raman", "when": "Mo`  

**Ava [5]:** Great, Olivia. Now let me find some checkup times for you next week. I have plenty of checkup times available next week. How about Monday, October 19 at 8:00 AM with Lena Fischer, NP? Or if you prefer a different day or time, I can show you other options.  
_(caller talked over this; heard only: "Great, Olivia. Now let me find some...")_  _(3.448s, 3 model calls)_

**Caller [6]:** sorry, you cut out, what was that?  
_(speech-to-text heard: "sorry you cut out what was that")_

**Ava [7]:** No problem. I found lots of checkup slots next week. How about Monday, October 19 at 8:00 AM with Lena Fischer, NP?  _(1.008s, 1 model calls)_

**Caller [8]:** yeah Monday the 19th at 8 AM works, I'll take that `[consents]`  
_(speech-to-text heard: "yeah monday the 19th at 8 am works i'll take that")_

**Ava [9]:** Just to confirm: Monday, October 19 at 8:00 AM with Lena Fischer, NP for your checkup. Is that correct?  _(0.858s, 1 model calls)_

**Caller [10]:** Yep that's right, sounds good. `[consents]`  
_(speech-to-text heard: "yep that's right sounds good")_

> `book_appointment({"slot_id": "S-FIS-1019-0800", "visit_type": "checkup", "reason": "checkup"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Monday, October 19 at 8:00 AM", "provider": "Lena Fischer, NP"}`  

**Ava [11]:** Perfect, Olivia. Your checkup is booked for Monday, October 19 at 8:00 AM with Lena Fischer, NP at Maple Street Family Clinic. Is there anything else I can help with?  _(2.09s, 2 model calls)_

**Caller [12]:** Nope that's all, thanks!  
_(speech-to-text heard: "nope that's all thanks")_

**Ava [13]:** You're welcome, Olivia. Thanks for calling Maple Street Family Clinic!  _(0.764s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1013 np_fischer 2026-10-19T08:00 checkup._

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
