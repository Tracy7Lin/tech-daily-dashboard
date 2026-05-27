## RAG And Boundaries

This subflow defines how the project research assistant should combine:

- runtime LLM reasoning
- report JSON retrieval
- future tool outputs
- boundary notes

### Core rule

Use the report knowledge layer as grounding, not as the only possible answer source.

The intended order is:

1. Try to retrieve relevant report evidence.
2. Let the LLM reason over the selected evidence.
3. If evidence is partial, allow model-extended explanation.
4. If evidence is absent, allow a general-reference answer with an explicit note.

### Grounding modes

Use these internal modes:

- `grounded`
  - report evidence is strong enough to support the answer directly
- `hybrid`
  - report evidence is relevant but incomplete, so the model may extend the answer
- `general`
  - the report knowledge layer does not directly cover the question, so the answer comes mainly from model knowledge

These modes are internal reasoning aids. The UI should expose only the minimum necessary note.

### Retrieval policy

Prefer the smallest useful context, not the largest one.

Good retrieval means:

- choose a few high-signal blocks
- prioritize dossier/tracking/cross-day/report blocks based on the question
- avoid dumping entire artifacts into the prompt when a few blocks are enough

### Boundary notes

- `grounded`
  - usually no explicit note is needed
- `hybrid`
  - note that the answer combines current report content with model inference
- `general`
  - explicitly note that the answer does not directly come from the current report and is for reference only

### Future tool integration

When tools are added later, the same pattern applies:

- tool output becomes an additional evidence source
- evidence attribution must say whether support came from:
  - report knowledge layer
  - tool output
  - model extension
  - general knowledge

Do not blur those boundaries.
