# JFB-004: Development experiment

## Task

Loss of precision in average calculation.

## Baseline validation

Maven compiled the project successfully.

Tests: 12. Failures: 3. Errors: 0. Skipped: 0.

The failures matched task.yaml:

- StatisticsServiceTest.averagePreservesPositiveFraction

- StatisticsServiceTest.averagePreservesNegativeFraction

- StatisticsServiceTest.averagePreservesFractionAcrossZero

## Gemma run

Model: gemma4:e2b-it-qat

Result: experiments/results/JFB-004_20261001T120036262415Z.json

- Status: PASSED.

- Selected files: 3.

- Changed files: 1.

- Prompt tokens: 3381.

- Output tokens: 318.

- Model duration: 249.84 seconds.

- Final tests: 12.

- Final failures: 0.

- Final errors: 0.

- Final skipped: 0.

## Repair inspection

The model changed MeanCalculator.java to convert the total to double

before division.

The patch contained one source-line change. Tests were unchanged.

## Generation metadata

- Schema version: 2.

- Done: true.

- Done reason: stop.

- Endpoint: /api/generate.

- Thinking: false.

- Temperature: 0.0.

- Context size: 4096.

- Maximum output tokens: 768.

- Seed: 42.

## Interpretation

This is a successful development run.

The new completion metadata and requested settings were verified in

the saved result JSON.

Controlled comparisons remain necessary to measure the effect of

graph-guided retrieval on repair performance.
