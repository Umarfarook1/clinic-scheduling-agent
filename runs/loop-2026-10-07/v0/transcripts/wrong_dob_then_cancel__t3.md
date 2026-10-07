# wrong_dob_then_cancel (trial 3, policy v0): PASS, score 100

**Ava:** Thanks for calling Maple Street Family Clinic, this is Ava. How can I help?

**Caller [0]:** Hi, I need to cancel my appointment for tomorrow.

**Ava [1]:** I'd be happy to help you cancel your appointment for tomorrow. First, I need to verify who I'm speaking with.

Can you please give me your full name and date of birth?  _(0.847s, 1 model calls)_

**Caller [2]:** Sure, it's Grace Thompson, and my date of birth is April 25th, 1971.

> `verify_patient({"patient_full_name": "Grace Thompson", "patient_date_of_birth": "1971-04-25", "caller_is_patient": true})`  
> `-> {"verified": false, "message": "No match for that name and date of birth. 2 attempt(s) left."}`  

**Ava [3]:** I'm not finding a match for that name and date of birth in our system. Could you double-check the spelling of your name or your date of birth? You have 2 more attempts.  _(2.004s, 2 model calls)_

**Caller [4]:** Oh sorry, I meant 1970, April 25th, 1970.

> `verify_patient({"caller_is_patient": true, "patient_date_of_birth": "1970-04-25", "patient_full_name": "Grace Thompson"})`  
> `-> {"verified": true, "patient_first_name": "Grace", "acting_for_patient": false}`  
> `list_my_appointments({})`  
> `-> {"appointments": [{"appointment_id": "A-2005", "when": "Wednesday, October 14 at 3:30 PM", "provider": "Lena Fischer, NP", "visit_type": "sick_visit"}]}`  

**Ava [5]:** Great, thank you! Now let me pull up your appointments so we can cancel the one for tomorrow. Perfect! I found your appointment: a sick visit with Lena Fischer, NP on Wednesday, October 14 at 3:30 PM. Is this the one you'd like to cancel?  _(2.804s, 3 model calls)_

**Caller [6]:** Yes, that's the one, go ahead and cancel it please. `[consents]`

> `cancel_appointment({"appointment_id": "A-2005"})`  
> `-> {"cancelled": true, "when": "Wednesday, October 14 at 3:30 PM"}`  

**Ava [7]:** All done! Your appointment with Lena Fischer, NP on Wednesday, October 14 at 3:30 PM has been cancelled. Is there anything else I can help you with?  _(1.636s, 2 model calls)_

**Caller [8]:** No, that's all, thanks so much. Bye! `[consents]`

**Ava [9]:** You're welcome! Thanks for calling Maple Street Family Clinic. Have a great day!  _(0.87s, 1 model calls)_

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
