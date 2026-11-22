# Single-host deployment

This guide runs the API and PostgreSQL on one Linux VM with Docker Compose. The included Compose credentials are for local development only. Use HTTPS at the public reverse proxy and keep PostgreSQL bound to localhost.

## 1. Prepare the host

Install Docker Engine and the Docker Compose plugin, clone this repository, and enter its directory. Create the environment file:

```sh
cp .env.example .env
```

Edit `.env` and set at least:

```dotenv
POSTGRES_PASSWORD=<unique URL-safe password>
ANTHROPIC_API_KEY=<your key>
CLAUDE_MODEL=<model available to your account>
ADMIN_TOKEN=<long random secret>
```

Generate URL-safe secrets with `openssl rand -hex 32`. Do not commit `.env`. Set `SUPPORT_EMAIL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_ADDRESS` to enable email handoff. Without SMTP settings, handoff messages are written to the app container's local outbox; configure persistent storage or SMTP before relying on that fallback in production.

If a separate website origin will embed the widget, set `CORS_ALLOW_ORIGINS` to its exact HTTPS origin, for example `https://shop.example.com`. Leave it empty for a same-origin widget.

## 2. Start and ingest

```sh
docker compose up -d --build
docker compose ps
docker compose exec app python -m app.ingest.pipeline /app/data/demo_site
```

The first start may take time while the local multilingual embedding model downloads into the named `model_cache` volume. The model is reused after restart. The Postgres data is kept in `postgres_data`. Back up both volumes before upgrades or host maintenance.

Confirm the API responds:

```sh
curl http://localhost:8000/health
curl http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quel est le prix de la baguette tradition ?"}'
```

The app initializes its schema at startup. Re-run the ingestion command after changing source documents.

## 3. Publish the widget

The demo is served at `https://YOUR_API_HOST/demo`; its script and demo source files are served by the same API origin. For another website, add the script tag and set the API URL to the public API origin:

```html
<script src="https://YOUR_API_HOST/widget/chat.js"
        data-api-url="https://YOUR_API_HOST/"
        data-title="Assistant FAQ"
        data-primary-color="#8f3e25"></script>
```

Place the API behind a TLS reverse proxy such as Caddy or Nginx. Restrict access to `/ingest` at the network layer as well as with `ADMIN_TOKEN`; do not expose PostgreSQL publicly. Set resource limits and configure regular database-volume backups.

## Required environment settings

| Variable | Purpose |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose database identity and password |
| `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` | Claude answering API |
| `ADMIN_TOKEN` | Protects the ingestion endpoint |
| `CORS_ALLOW_ORIGINS` | Exact browser origins allowed to call the API |
| `SUPPORT_EMAIL`, `SMTP_HOST`, `SMTP_FROM_ADDRESS` | Support handoff delivery |
| `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | Optional SMTP connection and login |
| `RETRIEVAL_VECTOR_THRESHOLD`, `RETRIEVAL_KEYWORD_THRESHOLD`, `RETRIEVAL_MIN_TERM_COVERAGE` | Tuned relevance and abstention gate |

Keep all credentials in the host's environment file or secret manager. Rotate them if they are exposed.
