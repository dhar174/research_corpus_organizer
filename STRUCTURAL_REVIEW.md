# Structural and Architectural Review

This review highlights high-level issues that can impact the overall workflow orchestration and downstream functionality.

## 1) Embedding stage never advances paper status
- The embedding worker builds the FAISS index but does not update any `PaperRecord.processing_status` values to `"embedded"`.【F:embedding_generator.py†L366-L439】【F:embedding_generator.py†L933-L989】
- Classification only selects papers whose status is `"embedded"`, `"deep_analyzed"`, or `"summarized"`, so nothing is ever eligible for classification after embeddings complete.【F:paper_classification.py†L495-L530】
- **Impact:** The classification stage will process zero papers even though embeddings exist, halting the intended pipeline.
- **Suggestion:** After successfully building and saving the FAISS index, iterate through `state["papers"]` and set each parsed paper to `"embedded"` (or introduce a dedicated transition step) so later stages can proceed.

## 2) "Ingestion only" execution still runs the full workflow
- `WorkflowExecutor.run_ingestion_only` is documented to stop after embeddings, but it constructs the full graph and invokes it without any guardrails or alternate routing.【F:workflow_orchestrator.py†L1014-L1041】
- **Impact:** Calling this helper unexpectedly runs summarization, taxonomy, classification, and export, which can be expensive and bypass manual review gates.
- **Suggestion:** Compile a graph that omits post-embedding nodes or configure the supervisor to route to `END` once embeddings finish when this mode is requested.

## 3) No fail-fast behavior when worker dependencies are missing
- The workflow graph always includes every stage, and the supervisor keeps routing based on `current_phase` and paper counts.【F:workflow_orchestrator.py†L377-L427】【F:workflow_orchestrator.py†L183-L249】
- Example: if `pdf_parser` is unavailable, the parse node only logs a warning but still sets `current_phase` to `"parsing"`, while papers remain `"pending"`. The supervisor then repeatedly routes back to `"parse"` forever.【F:workflow_orchestrator.py†L474-L510】【F:workflow_orchestrator.py†L203-L215】
- **Impact:** Missing optional dependencies lead to infinite loops rather than surfacing actionable errors or skipping stages.
- **Suggestion:** Before graph creation, drop nodes whose dependencies are absent or have the supervisor detect stalled progress and raise a clear error so execution can terminate gracefully.
