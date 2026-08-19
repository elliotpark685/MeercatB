# Scoped RAG retrieval evaluation

This package measures only the existing `LawSearchService` retriever. It does not alter law data, create a separate search algorithm, or include final LLM answer generation.

The current dataset is `datasets/scoped_safety_rule.json`: 50 questions scoped to `산업안전보건기준에 관한 규칙`. The runner passes that document name as the service's existing `law_scope` value.

Before it sends a smoke query or writes results, the runner validates every expected article ID, its chunk, and its non-null pgvector embedding. Any invalid entry stops the run; it is not counted as a retrieval failure.

## Run

From `backend/`:

```bash
python -m evaluation.run_evaluation
```

On a valid dataset and index, this writes UTF-8 JSON and Excel-friendly UTF-8-SIG CSV:

```text
evaluation/results/scoped_safety_rule_baseline.json
evaluation/results/scoped_safety_rule_baseline.csv
```

Metrics are Hit@1, Hit@3, Hit@5, MRR, and average retrieval latency. Latency includes query embedding, keyword/vector retrieval, and deterministic reranking; it excludes LLM answer generation.
