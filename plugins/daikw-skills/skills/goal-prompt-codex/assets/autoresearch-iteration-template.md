<!-- 外側ループの契約から埋める。未指定の数値上限や状態ファイルは追加しない。 -->

/goal {{ACTION_FOR_THE_AGREED_ITERATION}}

## Scope and Constraints
{{HYPOTHESIS_AND_ALLOWED_CHANGE}}
{{FIXED_INPUTS_ENVIRONMENT_AND_INVARIANTS}}
{{AUTHORIZED_ACTIONS_AND_EXISTING_RESOURCE_LIMITS}}

## Verification
{{ITERATION_VERIFIER_AND_EXPECTED_OBSERVATIONS}}

## Hand-off
{{EXISTING_RESULT_LOCATION_AND_REQUIRED_EVIDENCE}}
After this iteration and its verification, return the measured result to the outer loop for its keep/discard decision.
If the check fails, preserve the evidence and report this iteration as unsuccessful.
If execution is blocked, report the missing input or capability and the work not run.
Do not start another iteration or claim the global objective has been achieved.
