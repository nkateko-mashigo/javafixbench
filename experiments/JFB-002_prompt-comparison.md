\# JFB-002: Development experiment notes



\## Task

Incorrect loyalty discount calculation.



\## Model

gemma4:e2b-it-qat



\## Runs



\### Original prompt

Result: experiments/results/JFB-002\_20260929T161242493090Z.json



\- 4 tests, 2 failures.

\- Generated response contained no effective source change.

\- The original reporting code incorrectly counted the returned

&#x20; unchanged file as one changed file.



\### Revised prompt

Result: experiments/results/JFB-002\_20260930T083853764372Z.json



\- Added general instructions to reason from failing assertions,

&#x20; trace dependencies, and return actual source changes.

\- Fixed changed-file counting.

\- Selected files: 3.

\- Changed files: 0.

\- Tests: 4.

\- Failures: 2.

\- Prompt tokens: 2976.

\- Output tokens: 265.

\- Model duration: 184.39 seconds.



\## Outcome

The revised prompt did not produce an effective repair on this task.

The reporting fix correctly recorded zero changed files.



These are development runs. They do not establish whether

graph-guided retrieval improves repair performance.



\## Next steps

Preserve both results, expand and validate the benchmark, then

compare retrieval strategies using consistent model settings.

