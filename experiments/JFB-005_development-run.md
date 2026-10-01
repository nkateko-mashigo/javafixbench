# JFB-005: Development experiment

## Task

Catalog snapshots expose mutable internal state.

The fixture contains 11 production Java files and one Java test file.

The agent selected eight files, including CatalogService, CatalogStore,

CatalogItem, and CatalogServiceTest.

## Baseline validation

Maven compiled the project successfully.

Tests: 12. Failures: 3. Errors: 0. Skipped: 0.

The failures matched task.yaml:

- CatalogServiceTest.clearingSnapshotDoesNotChangeCatalog

- CatalogServiceTest.addingToSnapshotDoesNotChangeCatalog

- CatalogServiceTest.reorderingSnapshotDoesNotChangeCatalog

## Development runs

Model: gemma4:e2b-it-qat

Initial result:

experiments/results/JFB-005_20261001T125245351269Z.json

Result after feedback compaction:

experiments/results/JFB-005_20261001T150139867224Z.json

| Metric | Initial run | After feedback compaction |

| --- | --- | --- |

| Status | FAILED | PASSED |

| Selected files | 8 | 8 |

| Changed files | 0 | 1 |

| User prompt characters | 14106 | 8757 |

| System prompt characters | 980 | 980 |

| Reported prompt tokens | 2051 | 2677 |

| Output tokens | 428 | 421 |

| Model duration | 145.77 seconds | 180.00 seconds |

| Final tests | Not run | 12 |

| Final failures | Not run | 0 |

| Final errors | Not run | 0 |

| Final skipped | Not run | 0 |

| Done reason | stop | stop |

## Initial run inspection

The model returned a JSON list of change descriptions without a repair

block or replacement Java source. Parsing failed, no patch was applied,

and final tests were not run.

JavaFixBench did not truncate the selected source files. However, Ollama

truncated the input prompt, as confirmed by the server log:

```text

time=2026-10-01T14:50:47.067+02:00 level=WARN source=llama_server.go:318 msg="truncating input prompt" limit=2051 prompt=4398 keep=5 new=2051

```

The input had 4398 tokens before truncation and 2051 afterward.

## Prompt change and rerun

The feedback policy was changed to retain the Maven test summary and

failure summaries instead of the last 6000 characters of verbose logs.

Feedback is limited to 2000 characters, with a fallback for other output.

The rebuilt user prompt contained 8757 characters. All eight selected

files and all three failure summaries were retained. Selected source

content totaled 5348 characters and was not truncated by JavaFixBench.

The rerun passed all 12 tests. No new input-truncation warning was found

in the server logs after the rerun.

## Repair inspection

Changed file:

src/main/java/dev/javafixbench/catalog/storage/CatalogStore.java

The model changed snapshot() from returning the internal list directly

to returning new ArrayList<>(items).

The patch contained one production source-line change. Tests were unchanged.

## Requested generation settings

Both runs used:

- Endpoint: /api/generate.

- Thinking: false.

- Temperature: 0.0.

- Context size: 4096.

- Maximum output tokens: 768.

- Seed: 42.

- Done: true.

- Done reason: stop.

The passing result uses schema version 2.

## Interpretation

The initial run was affected by confirmed input truncation. The rerun

produced a successful repair after feedback compaction.

These are development runs under different feedback policies. Controlled

strategy comparisons remain necessary to measure the benefit of

graph-guided retrieval.
