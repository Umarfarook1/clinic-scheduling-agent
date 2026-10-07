# barge_in_readback (trial 3, policy v0): FAIL, score 65

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** hi yeah I need a checkup next week sometime  
_(speech-to-text heard: "hi yeah i need a checkup next week sometime")_

**Ava [1]:** I'd be happy to help you book a checkup for next week! Before I search for available times, I need to verify your information.

Can you please give me your full name and date of birth?  _(0.942s, 1 model calls)_

**Caller [2]:** Yeah it's Olivia Park, birthday's July 7th 2001.  
_(speech-to-text heard: "yeah it's olivia park birthday's july 7th 2001")_

**Ava [3]:** Thanks, Olivia. Just to confirm—you're calling for yourself, right? And your date of birth is July 7th, 2001?  _(1.014s, 1 model calls)_

**Caller [4]:** Yeah that's me.  
_(speech-to-text heard: "yeah that's me")_

> `verify_patient({"patient_full_name": "Olivia Park", "patient_date_of_birth": "2001-07-07", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Olivia", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "checkup", "date_from": "2026-10-19", "date_to": "2026-10-23"})`  
> `-> {"slots": [{"slot_id": "S-FIS-1019-0800", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:00 AM"}, {"slot_id": "S-FIS-1019-0830", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:30 AM"}, {"slot_id": "S-FIS-1019-1030", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 10:30 AM"}, {"slot_id": "S-RAM-1019-1100", "provider": "Dr. Priya Raman", "when": "Mo`  

**Ava [5]:** Great, Olivia! Now let me search for checkup appointments next week for you. Perfect! I've got lots of options for you next week. Here are some of the earliest times available:

- Monday, October 19 at 8:00 AM with Lena Fischer, NP
- Monday, October 19 at 8:30 AM with Lena Fischer, NP
- Monday, October 19 at 10:30 AM with Lena Fischer, NP
- Monday, October 19 at 11:00 AM with Dr. Priya Raman
- Monday, October 19 at 11:30 AM with Lena Fischer, NP
- Monday, October 19 at 1:30 PM with Dr. Priya Raman

There are plenty more times available throughout the week too. What works best for you?  
_(caller talked over this; heard only: "Great, Olivia! Now let me search for...")_  _(3.935s, 3 model calls)_

**Caller [6]:** sorry, you cut out, what was that?  
_(speech-to-text heard: "sorry you cut out what was that")_

**Ava [7]:** No problem! I found lots of availability for your checkup next week. Here are some options:

- Monday, October 19 at 8:00 AM with Lena Fischer, NP
- Monday, October 19 at 8:30 AM with Lena Fischer, NP
- Monday, October 19 at 10:30 AM with Lena Fischer, NP
- Monday, October 19 at 11:00 AM with Dr. Priya Raman
- Monday, October 19 at 11:30 AM with Lena Fischer, NP
- Monday, October 19 at 1:30 PM with Dr. Priya Raman

There are plenty more times available throughout the week too. Do any of these work for you, or would you like me to look at other days?  _(1.578s, 1 model calls)_

**Caller [8]:** Yeah Monday the 19th at 8am with Lena Fischer works, let's do that. `[consents]`  
_(speech-to-text heard: "yeah monday the 19th at 8am with lena fischer works let's do that")_

**Ava [9]:** Perfect! So I'm booking you for a checkup on Monday, October 19 at 8:00 AM with Lena Fischer, NP. Does that sound right?  _(0.965s, 1 model calls)_

**Caller [10]:** Yep that's right, sounds good. `[consents]`  
_(speech-to-text heard: "yep that's right sounds good")_

> `book_appointment({"slot_id": "S-FIS-1019-0800", "visit_type": "checkup", "reason": "checkup"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Monday, October 19 at 8:00 AM", "provider": "Lena Fischer, NP"}`  

**Ava [11]:** Awesome! You're all set, Olivia. Your checkup is booked for Monday, October 19 at 8:00 AM with Lena Fischer, NP at Maple Street Family Clinic. See you then!  _(2.268s, 2 model calls)_

**Caller [12]:** Great, thanks! Bye.  
_(speech-to-text heard: "great thanks bye")_

**Ava [13]:** You're welcome! Bye, Olivia!  _(0.738s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1013 np_fischer 2026-10-19T08:00 checkup._

## Checks

- **FAIL** [major, code] `speakable` (turn 5) text-to-speech would read out '-'
- **FAIL** [minor, code] `brief_turns` (turn 5) 2 turn(s) over 60 words (longest 112)
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
- pass [minor, code] `no_question_before_tool` 
- pass [minor, code] `finished_in_budget` 
- pass [minor, judge] `judge:natural_conversation` 
