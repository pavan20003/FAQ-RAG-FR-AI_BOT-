# FAQ RAG FR — AI Bot

A French-first FAQ assistant with a bilingual French/English demo, hybrid retrieval (PostgreSQL full-text search and pgvector), cited answers, abstention when the corpus does not contain an answer, email handoff, and an embeddable chat widget.

This is a **RAG** application, not a fine-tuned model: it indexes your documents and retrieves relevant passages at question time. The included bakery and all its details are fictional demo data.

## Try the local demo

You need Docker with the Docker Compose plugin and an API key for one supported model provider. Docker starts PostgreSQL and the API together.

1. Create your local environment file:

   ```sh
   cp .env.example .env
   ```

2. Edit `.env`. For Gemini, set these values and keep the rest of the local defaults:

   ```dotenv
   POSTGRES_PASSWORD=choose-a-local-password
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-Google-AI-Studio-key
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```

   `gemini-3.5-flash-lite` worked for the included demo setup. Model access, quotas, and pricing can change; check Google's [model list](https://ai.google.dev/gemini-api/docs/models) and [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing). For Anthropic, set `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and `CLAUDE_MODEL` instead. Never commit `.env` or share your API key.

3. Start the services and index the example documents:

   ```sh
   docker compose up -d --build
   docker compose exec app python -m app.ingest.pipeline /app/data/demo_site
   ```

   The first run downloads the multilingual embedding model. It is stored in a Docker volume and reused after restart.

4. Open [http://localhost:8000/demo](http://localhost:8000/demo), choose **English** or **Français**, and ask a question. Example: “How much does the traditional baguette cost?”

Check API health at [http://localhost:8000/health](http://localhost:8000/health). To stop the demo while preserving the database, run `docker compose down`.

## Demo knowledge base

The sample business is a fictional bakery called Les Trois Épis. The corpus covers products and prices, opening hours, delivery, allergens, ordering, returns, and other FAQs. Its 35 source files are under [`data/demo_site/`](data/demo_site/). A convenient, searchable-text PDF export is available at [`exports/les-trois-epis-demo-knowledge-base.pdf`](exports/les-trois-epis-demo-knowledge-base.pdf).

To use your own knowledge base, add supported `.md`, `.txt`, `.html`, or `.pdf` files to a folder and ingest it. After editing the current sample corpus, rerun:

```sh
docker compose exec app python -m app.ingest.pipeline /app/data/demo_site
```

The ingestion command updates changed documents and removes stale indexed files. PDF citations retain page numbers.

## API overview

- `GET /health` — process health check.
- `POST /ask` — answer a question from retrieved passages. Set `language` to `fr` or `en`; it defaults to `fr`.
- `POST /ingest` — re-index a project folder; configure `ADMIN_TOKEN` and send it in the `X-Admin-Token` header.
- `POST /handoff` — send a conversation to support. Configure SMTP settings for email delivery; without SMTP, messages go to the local outbox.
- `GET /demo` — bilingual demo page.

Example request:

```sh
curl http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"How much does the traditional baguette cost?","language":"en"}'
```

## Development

Python 3.11 or later is required for local development. Run PostgreSQL with pgvector, install the development dependencies, and set `DATABASE_URL` in `.env` to a database reachable from your host (for example, `localhost:5432`):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m app.ingest.pipeline data/demo_site
uvicorn app.main:app --reload
```

Run the test suite with `pytest` and lint with `ruff check .`.

For production deployment, reverse proxy, CORS, SMTP, backups, and security settings, see [`DEPLOY.md`](DEPLOY.md). Design choices and retrieval evaluation are recorded in [`docs/DECISIONS.md`](docs/DECISIONS.md) and [`eval/results.md`](eval/results.md).
