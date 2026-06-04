# AI Email Reading Agent

TQTech Software Engineer 2 assessment project. The app reads emails from a mock inbox, classifies every email as important or not important, stores processed email IDs to prevent duplicates, and shows important emails on a dashboard.

## Architecture

- Backend: Python, FastAPI, SQLAlchemy, SQLite.
- Email source: mandatory mock JSON dataset in `backend/data/mock_emails.json`.
- Classifier: deterministic rule-based classifier by default, with optional OpenAI fallback scaffold.
- Scheduler: FastAPI lifespan task polls the same processing service used by `POST /agent/run-once`.
- Frontend: React + Vite dashboard served on port `3000`.
- Docker: root `docker-compose.yml` starts backend and frontend together.

## Features

- Mock email reading with at least 10 sample emails.
- AI-style structured classification output:
  - `important`
  - `priority`
  - `category`
  - `reason`
- Important email notifications with sender, subject, priority, category, reason, and received time.
- Duplicate prevention using `processed_emails.email_id`.
- Defensive uniqueness on `notifications.email_id`.
- Manual agent execution from the dashboard.
- Background polling from `POLL_INTERVAL_SECONDS`.
- Priority sorting: HIGH, then MEDIUM, then LOW.

## How Email Reading Works

The default source is `EMAIL_SOURCE=mock`. The backend reads `MOCK_EMAIL_FILE`, parses each email, and sends it through the same processor used by the scheduler and the manual API endpoint. Non-mock sources are intentionally out of scope for the MVP.

Each mock email contains:

```json
{
  "id": "mock-001",
  "sender": "sender@example.com",
  "subject": "Subject",
  "body": "Email body",
  "received_at": "2026-06-04T08:05:00Z"
}
```

## How AI Classification Works

The classifier returns:

```json
{
  "important": true,
  "priority": "HIGH",
  "category": "SERVER_DOWN",
  "reason": "The email reports a production outage or service availability issue."
}
```

Rule-based behavior is the guaranteed path:

- Payment failure, billing issue, overdue invoice: important, HIGH, PAYMENT_ISSUE.
- Server down, outage, production incident: important, HIGH, SERVER_DOWN.
- Client complaint or escalation: important, HIGH, CLIENT_COMPLAINT.
- Urgent request or refund request: important, MEDIUM, URGENT_REQUEST.
- Subscription renewal or automated account notice: important, LOW, SUBSCRIPTION.
- Newsletter, promotional, spam: not important, LOW, SPAM.

If `AI_PROVIDER=openai` and `OPENAI_API_KEY` is set, the backend attempts OpenAI classification and falls back to rules if the API call or response validation fails.

## Duplicate Prevention

Before classifying an email, the processor checks `processed_emails` for the email ID. If the ID already exists, it skips the email. If the ID is new, the agent classifies the email, creates a notification only when important, and then writes the ID to `processed_emails`.

The processor always marks new emails as processed after classification, including unimportant emails. This prevents the same email from being repeatedly reclassified or shown again.

## Scheduler and Polling

The FastAPI app starts a background polling loop during application startup. It immediately runs the processor once, then repeats after `POLL_INTERVAL_SECONDS`. The scheduler calls the same `EmailProcessor.run_once()` method as `POST /agent/run-once`, so manual and scheduled behavior stay consistent.

## Dashboard

The React dashboard shows:

- Source, poll interval, database status, and last refresh time.
- HIGH, MEDIUM, and LOW notification counts.
- `Run Agent Now` button.
- Refresh button and auto-refresh every few seconds.
- Notification table sorted by priority.
- Last run summary showing fetched, classified, notification, duplicate, and ignored counts.

## Environment Variables

Copy `.env.example` to `.env` for local overrides.

| Variable | Default | Purpose |
| --- | --- | --- |
| `EMAIL_SOURCE` | `mock` | Email source. Only mock is supported in the MVP. |
| `MOCK_EMAIL_FILE` | `./data/mock_emails.json` | Path to the mock email dataset from the backend working directory. |
| `AI_PROVIDER` | `rules` | Use `rules` or optional `openai`. |
| `OPENAI_API_KEY` | empty | Optional OpenAI API key. Never commit a real key. |
| `POLL_INTERVAL_SECONDS` | `30` | Background polling interval. |
| `DATABASE_URL` | `sqlite:///./data/app.db` | SQLite database URL. |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins for the API. |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend build-time API base URL. |

## Local Setup

This repo uses Pixi as the root task runner and toolchain manager, with `uv`
for the Python backend and `pnpm` for the React frontend.

Install Pixi, then from the repository root:

```bash
pixi run install
```

Run the backend:

```bash
pixi run backend-dev
```

Run the frontend in another terminal:

```bash
pixi run frontend-dev
```

Open the dashboard at `http://localhost:3000`.

You can also run the package managers directly:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend
pnpm install
pnpm run dev
```

## Docker Setup

From the repository root:

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend dashboard: `http://localhost:3000`

## Free No-Card Deployment

Recommended deployment:

- Backend API: Render Free Web Service.
- Frontend dashboard: Cloudflare Pages.
- Database: keep the default SQLite database for the assessment demo.

This keeps the frontend on static hosting and runs the FastAPI scheduler on a
long-running backend service. SQLite data may reset on free hosting restarts or
redeploys, but the mock dataset is bundled and the scheduler repopulates the demo
notifications on startup.

### Backend on Render

Use the root `render.yaml` Blueprint, or create a Render Web Service manually
with these settings:

| Setting | Value |
| --- | --- |
| Root directory | `backend` |
| Runtime | Python |
| Build command | `pip install uv==0.8.24 && uv sync --frozen --no-dev` |
| Start command | `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free |

Backend environment variables:

| Variable | Value |
| --- | --- |
| `EMAIL_SOURCE` | `mock` |
| `MOCK_EMAIL_FILE` | `./data/mock_emails.json` |
| `AI_PROVIDER` | `rules` |
| `OPENAI_API_KEY` | empty unless intentionally using OpenAI |
| `POLL_INTERVAL_SECONDS` | `30` |
| `DATABASE_URL` | `sqlite:///./data/app.db` |
| `CORS_ORIGINS` | deployed Cloudflare Pages URL, for example `https://your-project.pages.dev` |

After deployment, verify:

```bash
curl https://your-render-service.onrender.com/health
```

### Frontend on Cloudflare Pages

Create a Cloudflare Pages project from the same GitHub repository:

| Setting | Value |
| --- | --- |
| Project root | `frontend` |
| Framework preset | Vite |
| Build command | `pnpm install --frozen-lockfile && pnpm run build` |
| Build output directory | `dist` |

Frontend environment variable:

| Variable | Value |
| --- | --- |
| `VITE_API_BASE_URL` | deployed Render backend URL, for example `https://your-render-service.onrender.com` |

After the frontend URL is known, update Render's `CORS_ORIGINS` to that exact
origin and redeploy the backend if needed.

### Deployment Verification

Before sharing the live demo, verify:

- `https://your-render-service.onrender.com/health` returns `status: ok`.
- The Cloudflare Pages dashboard loads without browser console CORS errors.
- Notifications appear after backend startup.
- `Run Agent Now` works from the deployed dashboard.
- The frontend was rebuilt after setting `VITE_API_BASE_URL`.

## Mock Data

The mock dataset includes urgent client complaints, payment failures, billing issues, server outages, production incidents, refund requests, subscription notices, automated account notices, newsletters, and promotional spam.

The scheduler processes this dataset at startup, so the dashboard should show important notifications shortly after the backend starts.

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Backend, database, source, provider, and scheduler status. |
| `GET` | `/notifications` | Important notifications sorted by priority and received time. |
| `POST` | `/agent/run-once` | Manually process the email source once. |
| `GET` | `/debug/processed` | Show processed email IDs for duplicate-prevention demos. |

Example:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/agent/run-once
curl http://localhost:8000/notifications
```

## Tests

Backend tests cover classifier rules, email reading, processor duplicate handling,
and API route behavior. Frontend tests cover API client behavior, notification
sorting, reusable dashboard components, and the main dashboard run flow.

The Pixi test tasks run the existing test framework commands and save
timestamped PDF reports under `reports/pdf/`. Each suite writes its own report:
`backend-test-report-YYYY-MM-DD-HH-mm.pdf` or
`frontend-test-report-YYYY-MM-DD-HH-mm.pdf`.

```bash
pixi run backend-test
pixi run frontend-test
```

Frontend build check:

```bash
pixi run frontend-build
```

Run backend tests, frontend tests, and the frontend build:

```bash
pixi run test
```

Direct framework commands still work for raw console-only runs:

```bash
cd backend
uv run pytest

cd ../frontend
pnpm run test
```

There is no CI workflow in this repository. If one is added later, run
`pixi run test` and upload `reports/pdf/*.pdf` as build artifacts.

## Limitations

- Gmail and IMAP are not implemented; mock mode is the complete MVP path.
- OpenAI classification is optional and falls back to rules on any error.
- SQLite is suitable for the assessment demo, not high-concurrency production workloads.
- SQLite data on free app hosting can be ephemeral across restarts and redeploys.
- There is no authentication layer.
- The frontend API URL is set at build time through `VITE_API_BASE_URL`.

## Future Improvements

- Add Gmail or IMAP readers with OAuth/secret management.
- Add a notification detail drawer and acknowledgement workflow.
- Add classifier audit history for every processed email.
- Add pagination/filtering for large inboxes.
- Add Postgres support if persistent hosted demo data becomes necessary.
