# Decisions

## Phase 0

- The API health endpoint reports process health and does not query Postgres. Database schema setup runs during application startup; Compose gates app startup on Postgres readiness.
- Vector width is read from the selected Sentence Transformers model at startup. `EMBEDDING_DIM` is an explicit override for controlled local tests and is not a second production dimension constant.
- Conversation IDs are separate from session IDs so multiple messages can be grouped while retaining the caller's session key.
- The model cache is a named Compose volume and is ignored by Git when stored under `data/` locally.
