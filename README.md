# ReachInbox Email Scheduler

A full-stack app for scheduling outreach emails. You sign in with Google, add sender identities, write a message, pick a start time, and the system sends it later, even if the server restarts in between.

I built this for the ReachInbox Software Development Intern assignment. Emails are sent through Ethereal (a fake SMTP inbox), so you can test everything without emailing real people.

**Demo video:** _add link here_
**Design reference:** [Figma file from the assignment](https://www.figma.com/design/kOTwGlESjijCYnMgtHfvfU/Outbox-Labs-Assignment?node-id=59-4050&p=f&m=dev)

---

## The problem

Sending an email at a future time sounds easy until real life gets in the way:

- The server restarts before the email is due.
- Many emails become due at the same moment.
- A sender hits its hourly sending limit.
- Two workers pick up the same email and send it twice.

This project is built around those cases. Scheduled emails are stored safely, recovered after a restart, spread out by per-sender rate limits, and protected against duplicate sends. No cron jobs are used.

---

## Features

- Google sign-in with server-side sessions and logout
- Multiple senders per user, each with its own hourly limit and minimum delay
- Compose screen with pasted addresses or CSV/TXT import, validation, and a start time (up to 10,000 recipients per campaign)
- Delayed jobs with BullMQ and Redis, so scheduled emails survive restarts
- Startup recovery that repairs any job missing from the queue
- Rate limiting that stays correct across several workers
- Rate-limited emails are postponed, never dropped
- Optional Slack alert when a sender reaches its hourly cap
- Email search powered by Elasticsearch
- Scheduled and Sent views with pagination, plus loading, empty and error states
- Authenticated queue view with Bull Board at `/admin/queues`

---

## Screenshots

| Login | Dashboard | Empty queue |
| --- | --- | --- |
| ![Login page](docs/screenshots/login.png) | ![Dashboard](docs/screenshots/dashboard.png) | ![Empty queue](docs/screenshots/empty-queue.png) |

---

## Tech stack

| Area | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Backend | Node.js, TypeScript, Express |
| Database | PostgreSQL with Prisma |
| Queue | BullMQ on Redis |
| Rate limiting | Redis with a Lua script |
| Search | Elasticsearch |
| Email | Nodemailer with Ethereal SMTP |
| Auth | Google OAuth 2.0 |
| Notifications | Slack OAuth v2 |
| Local setup | Docker Compose |

---

## How it works

```text
React dashboard
      │  HTTP-only session cookie
      ▼
Express API ── PostgreSQL (source of truth)
      │              │  campaign + emails + outbox events (one transaction)
      │              ▼
      │        Outbox publisher
      │              │  job id: email-{emailId}
      ▼              ▼
Elasticsearch    BullMQ + Redis (delayed jobs)
                        │
                        ▼
                  Email worker
                   ├─ Redis rate reservation
                   ├─ Slack alert when the hourly cap is hit
                   └─ Nodemailer → Ethereal SMTP
                        │
                        ▼
                  PostgreSQL status update
```

**Scheduling.** When a campaign is created, the API saves the campaign, its email rows and outbox events in a single database transaction. A publisher then adds one delayed BullMQ job per email using the ID `email-{emailId}`. Because the ID is deterministic, publishing is idempotent: retrying the handoff does not add a second job for the same email. PostgreSQL is the source of truth. The search index and any missing queue jobs can be rebuilt from it. Redis also holds rate-limit reservations and Slack alert de-duplication state, which are not stored in PostgreSQL.

**Restart recovery.** On startup, the app republishes pending outbox events and re-creates any job that exists in PostgreSQL but not in Redis. A small retry timer repeats this after temporary failures. It only retries recovery and does not schedule emails, so this is not cron-based scheduling.

**No duplicate sends.** Before sending, a worker claims the email with a conditional database update, so only one worker can win. The status becomes `SENT` only after the SMTP server accepts the message. If a crash happens after SMTP accepted the message but before the database was updated, no system can know the outcome for sure. The email is marked `DELIVERY_UNKNOWN` so it can be checked in Ethereal before any manual retry.

**Rate limiting.** Every sender has an `hourlyLimit` and a `minimumDelayMs` (defaults: 100 per hour and 2,000 ms, editable per sender in the dashboard). One Redis Lua script does the whole check atomically: it removes reservations older than an hour, checks the cap and spacing, then either reserves a slot or returns a retry time. Because it is atomic, multiple workers share the same limit safely. A rate-limited job goes back to the delayed state instead of failing. If Redis is unreachable, the worker sends nothing and reschedules the job.

**Slack alerts.** When a cap is hit, Redis makes sure only one alert is sent per rate-limit window. The worker uses the Slack token saved for that sender's owner (encrypted with AES-256-GCM). If Slack is not connected, the alert is skipped and emails keep going.

**Search.** Elasticsearch only finds candidate emails. The final results are loaded from PostgreSQL using the logged-in user's ID, so users only see their own data. If Elasticsearch is down, the API returns `503 SEARCH_UNAVAILABLE` rather than a misleading empty list.

---

## Project structure

```text
.
├── backend/             # Express API, BullMQ worker, Prisma schema and migrations
├── frontend/            # React + Vite dashboard
├── docker-compose.yml   # PostgreSQL, Redis, Elasticsearch
├── .env.example         # Template for environment variables
└── README.md
```

The repo is an npm workspace with two packages: `backend` and `frontend`. The database schema lives in `backend/prisma/schema.prisma`.

---

## Getting started

**You need:** Node.js 20+, npm, and Docker with Docker Compose.

**1. Clone the repo**

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

**2. Set up environment variables**

Copy `.env.example` to `.env` in the repository root and fill it in (see the table below). Create a free mailbox at [Ethereal Email](https://ethereal.email/) and put its SMTP username and password in `ETHEREAL_USER` and `ETHEREAL_PASSWORD`. The usual host and port are `smtp.ethereal.email` and `587`.

**3. Start PostgreSQL, Redis and Elasticsearch**

```bash
docker compose up -d postgres redis elasticsearch
```

**4. Install packages and prepare the database**

```bash
npm install
npm run db:generate --workspace backend
npm run db:deploy --workspace backend
```

**5. Run the app** (two terminals)

```bash
npm run dev:backend    # API and worker
npm run dev:frontend   # dashboard
```

Open **http://localhost:5173**. You can also check `http://localhost:3000/health` (API is running) and `http://localhost:3000/ready` (dependencies are reachable).

In development, Vite proxies `/api` to `http://localhost:3000`, so cookies work on one origin. In production, serve the frontend and `/api` from the same origin behind an HTTPS reverse proxy.

---

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | Redis for BullMQ and rate limiting |
| `ELASTICSEARCH_URL`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`, `ELASTICSEARCH_EMAIL_INDEX` | Elasticsearch connection and index name |
| `SESSION_SECRET` | Signs sessions and OAuth state (32+ characters) |
| `TOKEN_ENCRYPTION_KEY` | Encrypts Slack tokens at rest (32+ characters) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Google OAuth |
| `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_REDIRECT_URI` | Slack OAuth |
| `SLACK_BOT_TOKEN`, `SLACK_NOTIFICATION_CHANNEL_ID` | Optional development fallback for Slack |
| `ETHEREAL_HOST`, `ETHEREAL_PORT`, `ETHEREAL_USER`, `ETHEREAL_PASSWORD` | SMTP settings |
| `WORKER_CONCURRENCY` | Jobs processed at once (default 5) |
| `PROCESSING_STALE_AFTER_MS` | Time before a stuck job becomes `DELIVERY_UNKNOWN` (default 300000) |
| `OUTBOX_RETRY_INTERVAL_MS` | Recovery retry interval (default 5000) |
| `RATE_LIMIT_REDIS_PREFIX`, `SLACK_RATE_LIMIT_REDIS_PREFIX` | Redis key prefixes |
| `MIN_EMAIL_DELAY_MS`, `MAX_EMAILS_PER_HOUR_PER_SENDER` | Defaults for new senders (2000 ms and 100) |
| `FRONTEND_ORIGIN` | Redirect after OAuth (default `http://localhost:5173`) |

The values in `.env.example` are for local use only. Generate your own random secrets, never commit `.env`, and never put secrets in a `VITE_` variable because those end up in browser code.

---

## Google and Slack setup

**Google login (required).** Create an OAuth 2.0 client of type *Web application* in Google Cloud Console and add `http://localhost:3000/api/auth/google/callback` as an authorized redirect URI. Put the client ID, secret and redirect URI in `.env`. The backend exchanges the code on the server and gives the browser only an HTTP-only session cookie. Nothing is stored in localStorage.

**Slack (optional).** Create a Slack app with OAuth v2 enabled and add `http://localhost:3000/api/auth/slack/callback` as a redirect URL. Then click **Connect Slack** in the dashboard. To see an alert, set a sender's hourly limit to a small number, schedule more emails than that, and check the connected channel.

---

## API overview

Data routes need a logged-in session. The server works out ownership from the session, so the client never sends a `userId`.

| Method and path | Purpose |
| --- | --- |
| `GET /api/auth/google` | Start Google login |
| `GET /api/auth/me` | Current user |
| `POST /api/auth/logout` | End the session |
| `GET /api/auth/slack` | Start Slack connection |
| `GET /api/auth/slack/status` | Returns `{ connected: boolean }` only |
| `GET /api/senders`, `POST /api/senders` | List or create senders |
| `POST /api/campaigns` | Schedule a campaign (1 to 10,000 recipients) |
| `GET /api/emails/scheduled?page=1&pageSize=20` | Scheduled emails |
| `GET /api/emails/search` | Search by `q`, `status`, `campaignId`, `senderId`, `limit`, `page` |
| `GET /admin/queues` | Bull Board queue view |

Example campaign request:

```json
{
  "name": "Product launch",
  "senderId": "<sender UUID from GET /api/senders>",
  "subject": "A note for you",
  "body": "Hello",
  "recipients": ["person@example.test"],
  "startTime": "2026-10-01T10:00:00.000Z"
}
```

The sender owns the rate settings. If you include rate fields in the request, they must match the sender's current values.

---

## Testing

```bash
npm run typecheck
npm run build
npm test
```

By default, tests that need live PostgreSQL, Redis and Elasticsearch are skipped. To run them, start the Docker services and set `RUN_INTEGRATION_TESTS=1`.

```powershell
# Windows PowerShell
$env:RUN_INTEGRATION_TESTS='1'; npm test
```

```bash
# macOS / Linux
RUN_INTEGRATION_TESTS=1 npm test
```

In my most recent run, the default suite passed 13 tests (20 integration tests skipped) and the full suite passed all 33. These tests use real local services but a stubbed SMTP, so they do not prove delivery to a live Slack workspace or Ethereal inbox. After changing the schema, run `npx prisma validate --schema backend/prisma/schema.prisma`.

---

## Trade-offs and limitations

- **One SMTP account.** Each sender has its own visible name and address, but all mail goes out through the single Ethereal account in `.env`.
- **No cancel action.** There is no cancellation API yet, so the Cancel button is disabled on purpose instead of pretending to work.
- **Not exactly-once.** A crash right after SMTP accepts a message can leave it as `DELIVERY_UNKNOWN`, as explained above.
- **Rate slots are kept after SMTP failures.** Giving them back while other workers may be mid-send could push a sender over its cap.
- **Slack not verified live here.** The code path is tested, but a real alert needs your own Slack app and workspace.
- **Design.** The UI was built using the Figma file above as the reference. A detailed pixel-by-pixel comparison was not done.

---

## Author

**Swati Pathak**
