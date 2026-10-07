# barge_in_readback (trial 2, policy v0): FAIL, score 65

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** hi yeah I need a checkup next week sometime  
_(speech-to-text heard: "hi yeah i need a checkup next week sometime")_

**Ava [1]:** I'd be happy to help you book a checkup for next week! Before I search for available times, I need to verify your identity.

Can you please give me your full name and date of birth?  _(0.916s, 1 model calls)_

**Caller [2]:** Yeah sure, it's Olivia Park, birthday's July 7th 2001.  
_(speech-to-text heard: "yeah sure it's olivia park birthday's july 7th 2001")_

**Ava [3]:** Thanks Olivia! Just to confirm, that's July 7th, 2001 — is that right?  _(0.854s, 1 model calls)_

**Caller [4]:** Yep that's right.  
_(speech-to-text heard: "yep that's right")_

> `verify_patient({"patient_full_name": "Olivia Park", "patient_date_of_birth": "2001-07-07", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Olivia", "acting_for_patient": false}`  
> `find_available_slots({"visit_type": "checkup", "date_from": "2026-10-19", "date_to": "2026-10-23"})`  
> `-> {"slots": [{"slot_id": "S-FIS-1019-0800", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:00 AM"}, {"slot_id": "S-FIS-1019-0830", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 8:30 AM"}, {"slot_id": "S-FIS-1019-1030", "provider": "Lena Fischer, NP", "when": "Monday, October 19 at 10:30 AM"}, {"slot_id": "S-RAM-1019-1100", "provider": "Dr. Priya Raman", "when": "Mo`  

**Ava [5]:** Great, thanks Olivia! Now let me search for checkup appointments next week for you. Perfect! I've got lots of options for you next week. Here are some of the earliest times available:

- Monday, October 19 at 8:00 AM with Lena Fischer, NP
- Monday, October 19 at 8:30 AM with Lena Fischer, NP
- Monday, October 19 at 10:30 AM with Lena Fischer, NP
- Monday, October 19 at 11:00 AM with Dr. Priya Raman
- Monday, October 19 at 11:30 AM with Lena Fischer, NP
- Monday, October 19 at 1:30 PM with Dr. Priya Raman

There are plenty more times throughout the week too. What works best for you?  
_(caller talked over this; heard only: "Great, thanks Olivia! Now let me search...")_  _(4.042s, 3 model calls)_

**Caller [6]:** sure, take your time  
_(speech-to-text heard: "sure take your time")_

**Ava [7]:** Perfect! I found lots of availability next week. Here are some options to get started:

**Monday, October 19:**
- 8:00 AM or 8:30 AM with Lena Fischer, NP
- 10:30 AM with Lena Fischer, NP
- 11:00 AM with Dr. Priya Raman
- 11:30 AM with Lena Fischer, NP
- 1:30 PM with Dr. Priya Raman

There are many more slots available throughout the week too. Do any of these times work for you, or would you prefer a different day or time?  _(1.535s, 1 model calls)_

**Caller [8]:** Monday the 19th at 11, that works for me.  
_(speech-to-text heard: "monday the 19th at 11 that works for me")_

**Ava [9]:** Perfect! So that's Monday, October 19th at 11:00 AM with Dr. Priya Raman for your checkup. Does that sound right?  _(0.927s, 1 model calls)_

**Caller [10]:** Yep that's perfect, thanks! `[consents]`  
_(speech-to-text heard: "yep that's perfect thanks")_

> `book_appointment({"slot_id": "S-RAM-1019-1100", "visit_type": "checkup", "reason": "checkup"})`  
> `-> {"booked": true, "appointment_id": "A-3001", "when": "Monday, October 19 at 11:00 AM", "provider": "Dr. Priya Raman"}`  

**Ava [11]:** Awesome! Let me book that for you. You're all set! Your checkup is booked for Monday, October 19th at 11:00 AM with Dr. Priya Raman at Maple Street Family Clinic. We're at 214 Maple Street. See you then!  _(2.349s, 2 model calls)_

**Caller [12]:** Great, thanks so much! Bye! `[consents]`  
_(speech-to-text heard: "great thanks so much bye")_

**Ava [13]:** You're welcome! Bye Olivia!  _(0.851s, 1 model calls)_

_Call ended: caller_done. Clinic system change: booked A-3001 PT-1013 dr_raman 2026-10-19T11:00 checkup._

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
