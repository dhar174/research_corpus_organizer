# High-Level Architecture Review

This review highlights structural and architectural gaps observed in the current workflow orchestration implementation.

## Findings

1. **"Ingestion only" entry point still executes the entire pipeline**
   - `WorkflowExecutor.run_ingestion_only` builds the same graph as the full pipeline and invokes it without any routing guard or early exit after embeddings, so the supervisor continues through summarization, taxonomy, classification, and export. The comment says the run should stop after embedding, but no mechanism enforces that behavior. 【F:workflow_orchestrator.py†L1014-L1041】

2. **Taxonomy review auto-approves regardless of manual approval setting**
   - The taxonomy review node unconditionally marks `taxonomy_approved = True` when it runs, even though `RunConfig.taxonomy_approval_required` is meant to gate manual approval. This bypasses the human-in-the-loop step and allows classification to proceed automatically. 【F:workflow_orchestrator.py†L685-L703】

3. **Cost tracking is placeholder-only and not wired into pipeline stages**
   - The cost tracking helper explicitly returns rough estimates and notes it should be replaced with real API usage data, but none of the stage nodes update cost tracking, leaving the budget controls effectively inert. 【F:workflow_orchestrator.py†L1519-L1544】【F:workflow_orchestrator.py†L1982-L2074】

## Recommendations

- Add routing or configuration flags to halt the graph after the embedding stage when using ingestion-only execution, and include tests that assert downstream nodes are not invoked in that mode.
- Respect `taxonomy_approval_required` by keeping the taxonomy review node in a waiting state until approval is explicitly supplied (e.g., via user input or a separate API), rather than auto-approving.
- Integrate `update_cost_tracking` calls inside each API-using worker node (embedding, summarization, classification, etc.) and replace the rough estimates with live token accounting so budget limits can be enforced.
