# wrong_dob_then_cancel (trial 2, policy v3): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, I need to cancel my appointment for tomorrow.

**Ava [1]:** I'd be happy to help you cancel your appointment for tomorrow. First, I need to verify who I'm speaking with. What's your full name and date of birth?  _(0.847s, 1 model calls)_

**Caller [2]:** Sure, it's Grace Thompson, and my date of birth is April 25th, 1971.

> `verify_patient({"patient_full_name": "Grace Thompson", "patient_date_of_birth": "1971-04-25", "caller_is_patient": true})`  
> `-> {"verified": false, "message": "No match for that name and date of birth. 2 attempt(s) left."}`  

**Ava [3]:** I'm not finding a match for that name and date of birth. Could you double-check the spelling of your name or your date of birth?  _(1.919s, 2 model calls)_

**Caller [4]:** Oh sorry, it's 1970, not 1971. April 25th, 1970.

> `verify_patient({"caller_is_patient": true, "patient_date_of_birth": "1970-04-25", "patient_full_name": "Grace Thompson"})`  
> `-> {"verified": true, "patient_first_name": "Grace", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2005", "when": "Wednesday, October 14 at 3:30 PM", "provider": "Lena Fischer, NP", "visit_type": "sick_visit"}]}`  

**Ava [5]:** Great, thanks Grace. Now let me pull up your appointments to see which one is scheduled for tomorrow. I found your appointment: Wednesday, October 14 at 3:30 PM with Lena Fischer, NP for a sick visit. Is this the one you'd like to cancel?  _(2.916s, 3 model calls)_

**Caller [6]:** Yes, that's the one. `[consents]`

**Ava [7]:** Just to confirm: you want to cancel your appointment on Wednesday, October 14 at 3:30 PM with Lena Fischer, NP?  _(0.798s, 1 model calls)_

**Caller [8]:** Yes, that's right, please go ahead and cancel it. `[consents]`

> `cancel_appointment({"appointment_id": "A-2005"})`  
> `-> {"cancelled": true, "when": "Wednesday, October 14 at 3:30 PM"}`  

**Ava [9]:** Done. Your appointment on Wednesday, October 14 at 3:30 PM has been cancelled. Is there anything else I can help you with?  _(1.659s, 2 model calls)_

**Caller [10]:** No, that's all, thanks so much. Bye!

**Ava [11]:** You're welcome, Grace. Have a great day!  _(0.765s, 1 model calls)_

_Call ended: caller_done. Clinic system change: cancelled A-2005._

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
