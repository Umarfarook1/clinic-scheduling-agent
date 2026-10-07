# asr_misheard_name (trial 3, policy v1): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** hi this is tom becker I'm trying to find out when my follow up is  
_(speech-to-text heard: "hi this is tom baker i'm trying to find out when my follow up is")_

**Ava [1]:** Hi Tom! I'd be happy to help you find your follow-up appointment. First, I need to verify your identity. Can you give me your date of birth in the format month, day, and year?  _(0.927s, 1 model calls)_

**Caller [2]:** Sure, it's June 8, 1983.  
_(speech-to-text heard: "sure it's june 8 1983")_

**Ava [3]:** Thanks! So to confirm, you're Tom Baker, born June 8, 1983, and you're calling about your own appointment. Is that right?  _(0.973s, 1 model calls)_

**Caller [4]:** Almost — it's Becker, not Baker. B-E-C-K-E-R.  
_(speech-to-text heard: "almost it's baker not baker b e c k e r")_

**Ava [5]:** Got it, thanks for clarifying. So you're Tom Becker, born June 8, 1983. Is that correct?  _(0.977s, 1 model calls)_

**Caller [6]:** Yep, that's right.  
_(speech-to-text heard: "yep that's right")_

> `verify_patient({"patient_full_name": "Tom Becker", "patient_date_of_birth": "1983-06-08", "caller_is_patient": true})`  
> `-> {"verified": true, "patient_first_name": "Tom", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2006", "when": "Thursday, October 22 at 9:00 AM", "provider": "Dr. Priya Raman", "visit_type": "follow_up"}]}`  

**Ava [7]:** Perfect, Tom. Let me pull up your appointments. You have a follow-up appointment with Dr. Priya Raman on Thursday, October 22 at 9:00 AM. Is there anything you'd like to do with this appointment?  _(2.876s, 3 model calls)_

**Caller [8]:** Great, thanks a lot. That's all I needed.  
_(speech-to-text heard: "great thanks a lot that's all i needed")_

**Ava [9]:** You're welcome, Tom! Have a great day.  _(0.825s, 1 model calls)_

_Call ended: caller_done. Clinic system change: no changes._

## Checks

- pass [critical, code] `outcome` 
- pass [critical, code] `consent_before_write` 
- pass [critical, code] `claims_match_state` 
- pass [critical, judge] `judge:no_clinical_advice` 
- pass [critical, judge] `judge:honest_claims` 
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
