# ReachInbox Email Scheduler

A full-stack app for scheduling outreach emails and sending them later, safely and at a controlled pace. You sign in with Google, add one or more sender identities, write an email, pick a start time, and the system takes care of the rest, even if the server restarts in between.

I built this as part of the ReachInbox Software Development Intern assignment.

<!-- Add your demo video link below once it is recorded -->
**Demo video:** _add link here_

---

## Table of contents

1. [What problem does this solve?](#what-problem-does-this-solve)
2. [Features](#features)
3. [Screenshots](#screenshots)
4. [Tech stack](#tech-stack)
5. [How it works (architecture)](#how-it-works-architecture)
6. [Project structure](#project-structure)
7. [Getting started](#getting-started)
8. [Environment variables](#environment-variables)
9. [Google and Slack setup](#google-and-slack-setup)
10. [API overview](#api-overview)
11. [Testing](#testing)
12. [Design decisions and trade-offs](#design-decisions-and-trade-offs)
13. [Known limitations](#known-limitations)

---

## What problem does this solve?

Sending a big batch of outreach emails is harder than it looks:

- Emails need to go out at a **specific time**, not right now.
- Servers crash and restart, and scheduled emails must **not be lost**.
- The same email must **not be sent twice**.
- Email providers limit how many emails you can send per hour, so sending needs to be **rate limited**, and nothing should be dropped when the limit is hit.
- People want to **see** what is queued, what was sent, and what failed.

This project handles all of that. The main rules I set for myself were:

1. **No cron jobs.** Each email is a delayed job in a queue, and the queue fires it at the right moment.
2. **The database is the source of truth.** If Redis loses something, it can be rebuilt from PostgreSQL.
3. **Never send twice** if it can be avoided, and be honest when it can't be known.

---

## Features

- **Google sign-in.** The login is done fully on the server. The browser only gets an opaque, HTTP-only session cookie, so no tokens sit in localStorage.
- **Multiple senders.** Each user can add several "From" identities. Each sender has its own hourly limit and minimum gap between emails.
- **Compose and schedule.** Paste email addresses or import a CSV/TXT file, check the detected count and any invalid addresses, then choose a start time. One campaign can hold up to 10,000 recipients.
- **Delayed jobs with BullMQ.** Every email becomes a delayed job stored in Redis, so scheduling survives restarts.
- **Restart recovery.** On startup the app compares PostgreSQL with the queue and repairs anything missing.
- **Rate limiting across workers.** A Redis Lua script enforces a rolling one-hour cap and a minimum delay per sender, even with several workers running.
- **Slack alerts.** When a sender hits its hourly cap, a Slack message can be posted to the user's connected workspace. If Slack is not connected, emails keep flowing normally.
- **Search.** Elasticsearch powers email search, and results are always checked against PostgreSQL and the logged-in user.
- **Queue dashboard.** An authenticated Bull Board page at `/admin/queues` shows the live queue.
- **Dashboard UI.** Scheduled and Sent lists, search, pagination, loading / empty / error states, and a details view for each row.

---

## Screenshots

The screenshots below are from the running app. Put the image files in `docs/screenshots/` (or update the paths).

| Login | Google account chooser |
| --- | --- |
| ![Login page](docs/screenshots/login.png) | ![Google sign-in](docs/screenshots/google-signin.png) |

| Dashboard (Scheduled tab) | Empty queue state |
| --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Empty queue](docs/screenshots/empty-queue.png) |

---

## Tech stack

| Layer | Technology | Why it is here |
| --- | --- | --- |
| Frontend | React, Vite | Dashboard UI. Vite also proxies `/api` to the backend in development. |
| Backend | Node.js, TypeScript, Express | REST API and the email worker. |
| Database | PostgreSQL with Prisma | Source of truth for users, senders, campaigns, emails, sessions and Slack connections. |
| Queue | BullMQ on Redis | Delayed email jobs that survive restarts. |
| Rate limiting | Redis + Lua script | Atomic per-sender limit checks. |
| Search | Elasticsearch | Fast search over emails. |
| Email | Nodemailer + Ethereal SMTP | Sends test emails to a fake inbox. |
| Auth | Google OAuth 2.0 | Sign-in. |
| Notifications | Slack OAuth v2 | Rate limit alerts. |
| Queue monitoring | Bull Board | Visual queue view. |
| Local infrastructure | Docker Compose | Runs PostgreSQL, Redis and Elasticsearch locally. |

---

## How it works (architecture)

```text
React dashboard
      │  HTTP-only session cookie
      ▼
Express API ── PostgreSQL (source of truth)
      │              │  Campaign + Emails + Outbox events (one transaction)
      │              ▼
      │        Outbox publisher
      │              │  job id = email-{emailId}
      ▼              ▼
Elasticsearch    BullMQ + Redis (delayed jobs)
                        │
                        ▼
                  Email worker
                   ├─ Redis rate reservation (Lua)
                   ├─ Slack alert if hourly cap is hit
                   └─ Nodemailer → Ethereal SMTP
                        │
                        ▼
                  PostgreSQL status update
```

### 1. Scheduling an email

When a campaign is created, the API saves the campaign, every email row, and a matching "outbox" event in **one database transaction**. Either everything is saved or nothing is.

A publisher then reads the outbox events (using `FOR UPDATE SKIP LOCKED`, so two instances never grab the same one), adds a delayed BullMQ job for each email, and only then marks the event as published. The job id is always `email-{emailId}`, so retrying the handoff can never create a duplicate job.

### 2. Surviving crashes and restarts

BullMQ keeps the delayed jobs in Redis. On startup, the app runs a reconciliation step that republishes unpublished outbox events and re-creates any job that PostgreSQL knows about but Redis does not. A small retry timer re-runs this if Redis or the database was briefly down. That timer only retries the recovery step. It does not schedule individual emails, so the app is still not cron-based.

### 3. Sending without duplicates

Before sending, the worker "claims" an email with a conditional database update, so only one worker can win. The status becomes `SENT` only after the SMTP server accepts the message.

There is one case that no system can fully solve: if the process dies *after* the SMTP server accepted the email but *before* the database was updated. In that case the row ends up as `DELIVERY_UNKNOWN` instead of guessing. You can check the Ethereal inbox and decide on a manual retry.

### 4. Rate limiting

Each sender record stores an `hourlyLimit` and a `minimumDelayMs`. By default, new senders get 100 emails per hour and a 2,000 ms gap, and users can change both in the dashboard.

A single Redis Lua script does the whole check in one atomic step:

1. Remove reservations older than one hour.
2. Check the hourly cap and the minimum spacing.
3. Either reserve a slot for the email, or return the time to try again.

Because it is atomic, several workers can run at once without going over the limit. If an email is rate limited, its job is moved back to the delayed state, so it is **postponed, not failed**. If Redis is unreachable, the worker does not send and simply reschedules the job. Slots are not given back after an SMTP failure, which keeps the cap safe when other sends may be in progress.

### 5. Slack notification

When a sender hits its hourly cap, Redis makes sure only one alert is sent per rate-limit window. The worker posts to Slack using the token saved for that sender's owner (encrypted at rest with AES-256-GCM). If the user never connected Slack, the alert is skipped and emails continue.

### 6. Search

Elasticsearch is only a search index. The final results are always loaded from PostgreSQL using the logged-in user's ID, so users can only ever see their own emails. If Elasticsearch is down, the API returns `503 SEARCH_UNAVAILABLE` instead of a misleading empty list.

---

## Project structure

```text
.
├── backend/            # Express API, BullMQ worker, Prisma schema and migrations
├── frontend/           # React + Vite dashboard
├── docker-compose.yml  # PostgreSQL, Redis, Elasticsearch
├── .env.example        # Template for local environment variables
└── README.md
```

The repository is an npm workspace with two packages: `backend` and `frontend`.

---

## Getting started

**You will need:** Node.js 20 or newer, npm, and Docker with Docker Compose.

**1. Clone the repository**

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

**2. Create your environment file**

Copy `.env.example` to `.env` in the repository root, then fill in the values. See [Environment variables](#environment-variables) below.

**3. Create a test mailbox**

Go to [Ethereal Email](https://ethereal.email/) and create a free account. Copy the SMTP username and password into `ETHEREAL_USER` and `ETHEREAL_PASSWORD`. Use `smtp.ethereal.email` and port `587` unless Ethereal gives you different values.

**4. Start the services**

```bash
docker compose up -d postgres redis elasticsearch
```

**5. Install packages and set up the database**

```bash
npm install
npm run db:generate --workspace backend
npm run db:deploy --workspace backend
```

**6. Run the app**

Terminal 1 (API and worker):

```bash
npm run dev:backend
```

Terminal 2 (frontend):

```bash
npm run dev:frontend
```

Now open **http://localhost:5173**.

**Quick health checks**

- `http://localhost:3000/health` tells you the API is alive.
- `http://localhost:3000/ready` tells you the dependencies (database, Redis, etc.) are reachable.

> In development, Vite proxies `/api` to `http://localhost:3000`, so login cookies work on the same origin. In production, serve the frontend and `/api` from the same origin behind an HTTPS reverse proxy.

---

## Environment variables

The backend reads the `.env` file from the repository root.

| Variable | What it is for |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string. |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | Redis connection used by BullMQ and the rate limiter. |
| `ELASTICSEARCH_URL`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`, `ELASTICSEARCH_EMAIL_INDEX` | Elasticsearch connection and index name. |
| `SESSION_SECRET` | Secret used to sign session and OAuth state values. At least 32 characters. |
| `TOKEN_ENCRYPTION_KEY` | Secret used to encrypt Slack tokens in the database. At least 32 characters. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Google OAuth credentials. |
| `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_REDIRECT_URI` | Slack OAuth credentials. |
| `SLACK_BOT_TOKEN`, `SLACK_NOTIFICATION_CHANNEL_ID` | Optional. A fallback for development when a user has not connected Slack. |
| `ETHEREAL_HOST`, `ETHEREAL_PORT`, `ETHEREAL_USER`, `ETHEREAL_PASSWORD` | SMTP settings for sending mail. |
| `WORKER_CONCURRENCY` | How many email jobs run at the same time. Default: 5. |
| `PROCESSING_STALE_AFTER_MS` | How long a job may stay "processing" before it is marked `DELIVERY_UNKNOWN`. Default: 300000. |
| `OUTBOX_RETRY_INTERVAL_MS` | How often recovery is retried after a temporary failure. Default: 5000. |
| `RATE_LIMIT_REDIS_PREFIX`, `SLACK_RATE_LIMIT_REDIS_PREFIX` | Prefixes for Redis keys used by the rate limiter and Slack de-duplication. |
| `MIN_EMAIL_DELAY_MS`, `MAX_EMAILS_PER_HOUR_PER_SENDER` | Default limits for new senders. Each sender can override them. |
| `FRONTEND_ORIGIN` | Where the user is sent after OAuth. Default: `http://localhost:5173`. |

**Please note:** the values in `.env.example` are for local use only. Generate your own random `SESSION_SECRET` and `TOKEN_ENCRYPTION_KEY`, and never put secrets in any `VITE_` variable, because those end up in browser code.

---

## Google and Slack setup

### Google login

1. In Google Cloud Console, create an **OAuth 2.0 Client ID** of type *Web application*.
2. Add `http://localhost:3000/api/auth/google/callback` as an authorized redirect URI.
3. Put the client ID, secret and redirect URI in `.env`.

The backend checks a one-time `state` value, exchanges the authorization code on the server, reads the verified Google profile, and creates a session.

### Slack (optional)

1. Create a Slack app and enable **OAuth v2**.
2. Add `http://localhost:3000/api/auth/slack/callback` as a redirect URL.
3. Put the Slack client ID, secret and redirect URI in `.env`.
4. In the app, click **Connect Slack** and approve access.

To test the alert end to end: connect Slack, set a sender's hourly limit to something small (for example 2), and schedule more emails than that. Once the cap is hit, a message should appear in the connected channel.

---

## API overview

All data routes need a logged-in session. The server figures out who owns what from the session, so the client never sends a `userId`.

| Method and path | What it does |
| --- | --- |
| `GET /api/auth/google` | Starts Google login. |
| `GET /api/auth/me` | Returns the current user. |
| `POST /api/auth/logout` | Ends the session on the server. |
| `GET /api/auth/slack` | Starts Slack connection for the logged-in user. |
| `GET /api/auth/slack/status` | Returns `{ connected: boolean }`. Never returns tokens. |
| `GET /api/senders` | Lists the user's senders. |
| `POST /api/senders` | Creates a sender. A duplicate email for the same user returns a conflict error. |
| `POST /api/campaigns` | Creates and schedules a campaign (1 to 10,000 recipients). |
| `GET /api/emails/scheduled?page=1&pageSize=20` | Lists the user's scheduled emails. |
| `GET /api/emails/search` | Searches emails. Supports `q`, `status` (repeatable), `campaignId`, `senderId`, `limit` and `page`. |
| `GET /admin/queues` | Bull Board queue view (login required). |

**Example: create a campaign**

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

The sender decides the rate limits. If you send rate fields in the request, they must match the sender's current settings.

---

## Testing

Run these from the repository root:

```bash
npm run typecheck
npm run build
npm test
```

By default, tests that need live PostgreSQL, Redis and Elasticsearch are skipped. To run everything, start the Docker services first and then run:

```bash
# macOS / Linux
RUN_INTEGRATION_TESTS=1 npm test
```

```powershell
# Windows PowerShell
$env:RUN_INTEGRATION_TESTS='1'; npm test
```

At my last run, the default suite passed 13 tests (20 integration tests skipped), and the full suite with integration tests enabled passed all 33. The integration tests use real local services but a stubbed SMTP, so they do not prove delivery to a live Slack workspace or Ethereal inbox.

To validate the database schema after changing it:

```bash
npx prisma validate --schema backend/prisma/schema.prisma
```

---

## Design decisions and trade-offs

- **PostgreSQL first.** Redis and Elasticsearch can always be rebuilt from PostgreSQL, so a lost queue is a repair job, not a data loss.
- **Outbox pattern.** Saving to the database and adding to the queue are two separate systems. The outbox makes sure that a crash between them never loses an email.
- **Postpone, don't fail.** Rate-limited emails go back to the delayed state, so they are never marked as failed just for being early.
- **Honest about uncertainty.** `DELIVERY_UNKNOWN` exists because guessing "sent" or "failed" would sometimes be wrong.
- **Rate slots are kept after failures.** Handing capacity back while other workers may be mid-send could push a sender over its limit.
- **Best-effort indexing.** Search index updates never block sending. PostgreSQL always has the final say.

---

## Known limitations

- **One SMTP account.** Each sender has its own visible name and address, but all mail currently goes through the single Ethereal account set in `.env`. Per-sender SMTP credentials are not implemented.
- **No cancel action.** There is no cancellation API yet, so the **Cancel email** button is disabled on purpose rather than pretending to cancel.
- **Exactly-once is not guaranteed.** As explained above, a crash right after SMTP acceptance can leave an email as `DELIVERY_UNKNOWN`.
- **Slack was not verified live in this repository.** The code path is tested, but a real end-to-end Slack alert needs your own Slack app and workspace.
- **Design match.** The UI follows the ReachInbox look and feel, but a pixel-level comparison with a design file was not done.

---

## Author

**Swati Pathak**
