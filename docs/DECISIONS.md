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
