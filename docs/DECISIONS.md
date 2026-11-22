# Decisions

## Phase 0

- The API health endpoint reports process health and does not query Postgres. Database schema setup runs during application startup; Compose gates app startup on Postgres readiness.
- Vector width is read from the selected Sentence Transformers model at startup. `EMBEDDING_DIM` is an explicit override for controlled local tests and is not a second production dimension constant.
- Conversation IDs are separate from session IDs so multiple messages can be grouped while retaining the caller's session key.
- The model cache is a named Compose volume and is ignored by Git when stored under `data/` locally.

## Phase 2

- Chunk sizes use whitespace-delimited words as an approximate token count. This keeps chunking dependency-free and understandable; model tokenizers can be considered later if evaluation shows a need.
- Headings are parsed from Markdown heading syntax. PDF page text is split page by page, so citations can retain one-based page numbers.
- Ingestion computes local embeddings before replacing database rows, then commits changed documents and removed files together in one database transaction.
- HTML is parsed with Beautiful Soup's built-in HTML parser. Navigation, footer, scripts, styles, and noscript elements are removed before text extraction.

## Phase 3

- Keyword search splits a user's plain-text query into word tokens and joins them with `OR` before passing them to PostgreSQL's French `websearch_to_tsquery`. This avoids interpreting user input as raw `tsquery` syntax while allowing a match on any useful term.
- Hybrid retrieval fuses up to 20 vector and 20 keyword candidates with reciprocal rank fusion using `k=60`, then returns the five highest-scoring results.
- The relevance gate accepts a result that clears the vector similarity floor or one that clears the keyword rank floor and covers enough non-stopword query terms. These defaults are tunable in environment settings and will be evaluated in Phase 6.

## Phase 4

- The LLM is created only after retrieval passes the relevance gate, so an abstention works without an API key and never calls Claude.
- Retrieved text and attributes are escaped inside numbered passage tags. The system prompt treats these passages as untrusted data and tells the model to ignore instructions found inside them.
- The server removes citations that do not point to one of the retrieved passages and builds source metadata from those passages, never from generated text.
- A request logs both the user question and the assistant response with source metadata, abstention status, latency, and the session's conversation ID.

## Phase 6

- The 50 evaluation questions use stable `(source, heading)` labels so re-ingestion can change database IDs without invalidating the gold set. The question order is shuffled with seed 42 and stratified before saving: each half has 20 answerable and 5 unanswerable questions.
- Recall@5 is the mean fraction of a question's gold source-heading pairs found in the first five results. MRR uses the rank of the first matching pair. Mean retrieval latency includes local query embedding and database search time.
- Gate thresholds are tuned for balanced accuracy on the first 25 questions only, then frozen for the last 25. The in-memory API gate stays dependency-free; tuning results belong in `.env.example` defaults only after the real evaluation has run.
- The optional faithfulness CSV is deliberately ungraded: a human fills in the support column after reviewing cited answers.

## Phase 7

- The widget uses a Shadow DOM to keep its styles isolated and `textContent` for all API-provided text. Source links resolve through the API's demo-data route; a production corpus should replace these with stable public URLs.
- The demo page is served by FastAPI on the same origin as the API, so trying it does not require a permissive CORS rule. Embedding on a different site requires adding that exact origin to the CORS allow-list.
- The container installs a pinned CPU-only PyTorch wheel because the API runs embeddings on CPU and does not need CUDA packages. The model weights remain in a persistent named volume.
