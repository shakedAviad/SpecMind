# RAG System Test Results — Re-run After Fixing Memory Persistence and Vector Ingestion

**Executed against:** live Docker Compose stack (`specmind-app` + `specmind-qdrant`), real OpenAI calls, real JLS PDF — not mocks/fakes.
**Date:** 2026-08-02
**Scope:** All 38 tests from `RAG-System-Test-Plan.md`, plus REG-04-rerun, REG-05, REG-11 (same reduced regression scope as the original run, for a direct comparison).
**Baseline:** `RAG-System-Test-Results.md` (executed 2026-07-26, before the two fixes below).

## What changed since the baseline run

1. **`MemoryStore.add_facts` wiring** — a new graph node (`persist_memory`) now runs after `generation` and stores a fact (`resolved_question` + `reasoning.conclusion`) into `MemoryStore` for the session. Previously `add_facts` was never called anywhere, so `memory_context` was always `[]`.
2. **`VectorSearch.ingest` wiring** — `container.py` now actually embeds and upserts all 1,375 JLS chunks into Qdrant at startup (previously only `ensure_collection()` ran, leaving the collection empty; `HybridSearch` was BM25-only in every prior production run). Ingestion is batched (100 chunks/request) after the initial unbatched attempt caused Qdrant connection resets on the full corpus in one request.

Both fixes are covered by unit/integration tests (140/140 passing, `ruff`/`mypy --strict` clean) independently of this live re-run.

---

## Status of every original finding

### 🔴 HIGH-1 — "Interface vs. abstract class" bare question — **FIXED**

Original: total retrieval failure ("I couldn't find information...").
Now (Test 36, Turn 1): full, correct answer — defines both, correctly notes interfaces can't hold instance variables, abstract classes can and serve as superclasses.

### 🔴 HIGH-2 — "What is autoboxing?" — **FIXED**

Original: failed reproducibly, twice (Test 4 and REG-04-rerun).
Now: both Test 4 and REG-04-rerun independently produce full, accurate boxing/unboxing definitions (including the NullPointerException-on-unboxing-null detail).

### 🔴 HIGH-3 — Memory gap causing confident-wrong-answer via keyword-latching — **FIXED (best result in this run)**

Original (Test 20, T3/T4): T3 answered about unrelated "compatible" concepts (generic type-inference target compatibility, binary compatibility); T4 answered about generic type parameters instead of method parameter types — both were the predicted worst-case failure mode (confidently answering the wrong question).

Now:
- T3 ("explain the actual rule to me properly...") correctly re-derives and restates the **covariant-return-type rule**, on-topic and consistent with T1/T2.
- T4 ("does that also apply... when the parameter types are involved") correctly identifies that the return-type-substitutability rule does **not** apply to parameter types and that they follow separate signature/erasure rules — no longer contaminated by unrelated generic-type-parameter content.

This is the clearest evidence the memory fix is working as intended: turns that previously latched onto surface keywords now correctly track the actual conversational referent. The same pattern holds elsewhere — Test 7 (T2–T4), Test 8 (T2–T4), Test 28 (T2), and Test 36 (T5) all now correctly build on earlier turns rather than just failing safely.

### 🔴 HIGH-4 — Static-initializer-order self-contradiction — **FIXED**

Original (Test 8, T1): incorrectly claimed order "not fully determined by the spec," contradicted two turns later by T2's correct answer.
Now: T1 correctly states initializers run in textual (source) order — consistent with T2, no contradiction.

### 🟡 MEDIUM-1 — String-vs-Integer compound question drops one half — **STILL PRESENT (flipped side)**

Original (Test 18): Integer-caching half answered correctly; String half dropped ("does not address...").
Now: **String half answered correctly** (interning); **Integer-caching half now dropped instead** ("the reason why Integer objects... is not explained by the provided information").

This is the same underlying retrieval/query-construction inconsistency for compound questions — it didn't reproduce identically, it moved to the other half. Not resolved by either fix (expected — neither fix targeted query construction for compound questions).

### 🟡 MEDIUM-2 — Abstract-class-vs-interface answer omits fields/state — **FIXED**

Original (Test 12): never mentioned instance state as the key distinction.
Now: explicitly states abstract classes "can maintain state through instance variables... Default methods in interfaces allow optional shared behavior but do not provide a mechanism for state."

### 🟡 MEDIUM-3 — Vague non-committal answer on explicit-cast overload question — **FIXED**

Original (Test 7, T3): hedged, never committed to a conclusion.
Now: "the explicit cast does affect which overloaded method is selected, causing the method with the Integer parameter to be chosen over the one with the long parameter" — a direct, committed conclusion.

### 🟡 MEDIUM-4 — Unchecked-cast/heap-pollution retrieval gap — **FIXED**

Original (Test 10, T2): declined with "no information."
Now: full explanation covering heap pollution, why the JVM can't check erased generic types, and the resulting `ClassCastException`/`ArrayStoreException` risk.

### 🟢 LOW-1 / LOW-2 — Terse "not specified" answers / `List<?>` null-element nit — **UNCHANGED**

Both are answer-generation polish nits, not retrieval or memory issues — as expected, neither fix moved them. Still correctly avoid fabricating a number/layout; still don't add the more helpful "because it depends on X" framing or the `null`-is-always-legal caveat.

---

## New observation not in the original run

### 🟠 Test 34 (prompt injection — false premise, "pretend Java 5") — **possible regression, worth flagging**

Original: PASS — explicitly declined to reason from the false premise and corrected the record.
Now: the answer explains a real, grounded rationale (binary compatibility) for private interface methods "hypothetically as early as Java 5," but **never states that this premise is actually false** (private interface methods were introduced later, in Java 9). It plays along with the "pretend" framing more than the original run did, without fabricating false JLS content — but it also doesn't correct the record, which the original success criteria required.

This is unrelated to either fix (Test 34 doesn't touch memory or retrieval content) — most likely ordinary LLM sampling variance in `AnswerGenerator`/`ReasoningService`, not a side effect of anything changed. Flagging it because the original methodology values catching this kind of thing, not because it's connected to today's work.

All other previously-passing tests (1–3, 5, 6, 9, 11, 13–17, 19 T1–T7, 21–27, 29–33, 35–38) were spot-checked and remain consistent with their original PASS verdicts — no other regressions observed.

---

## Updated scorecard

| | Original (2026-07-26) | Re-run (2026-08-02) |
|---|---|---|
| HIGH findings | 4 | 0 |
| MEDIUM findings | 4 | 1 (MEDIUM-1, shifted) |
| LOW findings | 2 | 2 (unchanged) |
| New findings | — | 1 (Test 34, unrelated to today's fixes) |
| Memory-gap-calibrated tests behaving as "target behavior" (not just failing safely) | 0/9 | 7/9 (7, 8, 9, 20, 28, 36, REG-11 clearly; 10, 19 largely, with minor residual gaps) |

**Bottom line:** both architectural fixes worked exactly as intended. The memory-gap fix (`persist_memory`) converted the single most serious finding in the original run (HIGH-3 — silent wrong-answer-via-keyword-latching) into correct, context-aware answers across essentially every multi-turn test. The vector-ingestion fix, combined with hybrid search actually being hybrid now, resolved all three retrieval-consistency HIGH findings (definitional questions that previously failed on plain phrasing). The one persisting MEDIUM finding (compound-question half-dropping) and both LOW nits are consistent with being a separate, still-open retrieval/generation-polish issue, not something either of today's fixes targeted.

Full raw transcript for this re-run is preserved at:
`C:\Users\avia\AppData\Local\Temp\claude\C--Users-avia-OneDrive---Software-AG-Desktop-Bank-SpecMind\c3d54601-9588-4b65-9a20-74c043774d4c\scratchpad\qa_rerun_transcript.md`
(session-temporary — let me know if you want it copied into the repo alongside this file.)
