# ReachInbox Email Scheduler

ReachInbox is a full-stack email scheduling application built for the Software Development Intern assignment. It lets a signed-in user connect sender identities, prepare a message for one or more recipients, and schedule delivery for a chosen time. The dashboard also shows scheduled and completed email activity.

The project focuses on the parts that make a scheduler dependable: persistent jobs, restart recovery, safe processing across workers, and sender-level rate limits. Email delivery uses Ethereal, so messages can be inspected in a test inbox without contacting real recipients.

## What problem this solves

Sending a message at a future time is straightforward until a process restarts, several jobs become due together, or a sender reaches a provider limit. A dependable scheduler must retain the work, avoid accidental duplicate sends, and defer messages safely when sending capacity is unavailable.

This project combines a web dashboard with an API and background worker. PostgreSQL stores application and delivery state, BullMQ and Redis manage delayed work, and the worker sends due email through Ethereal SMTP. The React dashboard gives users a place to compose, schedule, search, and review messages.

## Features

- Google OAuth sign-in, server-side sessions, and logout.
- User-owned sender accounts with configurable hourly limits and minimum spacing.
- Email composition with pasted recipients or CSV/TXT import, recipient validation, and scheduled start time.
- Persistent delayed jobs managed by BullMQ; no cron scheduler is used.
- PostgreSQL-backed campaign, recipient, session, sender, and delivery state.
- Transactional outbox and startup reconciliation to recover queue handoffs and missing jobs.
- Worker concurrency configured through the environment.
- Atomic Redis-based per-sender rate reservations shared across workers.
- Rescheduling when a sender reaches its hourly limit, rather than dropping the job.
- Slack OAuth connection and rate-limit notifications when the user has connected Slack.
- Ethereal SMTP delivery for safe testing.
- Search backed by Elasticsearch, with results checked against PostgreSQL ownership and status.
- Scheduled and sent/failed email views, pagination, status details, and empty/loading/error states.
- Authenticated Bull Board queue visibility.

## Screenshots

The sign-in screen uses Google OAuth. The workspace provides a scheduled-email queue and navigation to sent messages and email composition.

## Architecture

```text
React + TypeScript dashboard
            │
            │ HTTP requests with an HTTP-only session cookie
            ▼
      Express + TypeScript API ───────────────► Elasticsearch
            │                                    derived search index
            │ PostgreSQL transaction
            ├── campaign and email rows
            └── outbox events
                     │
                     ▼
              Outbox publisher
                     │ deterministic job ID: email-{emailId}
                     ▼
             BullMQ delayed queue ◄──────────► Redis
                     │
                     ▼
                Email worker
                 ├── Redis atomic sender rate reservation
                 ├── Slack notification when an hourly cap is reached
                 └── Nodemailer ─────────────► Ethereal SMTP
                     │
                     ▼
              PostgreSQL delivery state
```

### Scheduling and restart recovery

PostgreSQL is the source of truth for campaigns and email state. When a campaign is created, the API writes its campaign, email rows, and outbox events in one database transaction. The outbox publisher claims pending events with `FOR UPDATE SKIP LOCKED`, adds BullMQ jobs using deterministic IDs, and marks events as published after the queue accepts them.

BullMQ delayed jobs determine when an email becomes eligible to run. On startup, reconciliation republishes pending outbox events and repairs missing queue jobs from PostgreSQL. A retry timer runs reconciliation after temporary infrastructure failures; it does not schedule individual emails and is not a cron job.

The worker claims eligible email rows with conditional database updates before sending. This makes concurrent processing safer and prevents already-sent rows from being sent again. If the worker loses its connection after the SMTP server may have accepted a message but before PostgreSQL records the result, the outcome is marked `DELIVERY_UNKNOWN`. SMTP cannot provide an exactly-once guarantee across that failure window, so an unknown delivery should be checked in Ethereal before retrying manually.

### Rate limits and worker concurrency

Each sender has its own `hourlyLimit` and `minimumDelayMs`. The default values for newly created senders are 100 messages per hour and 2,000 milliseconds between sends; the defaults can be changed with environment variables, and a sender can have its own values in the dashboard. Campaigns using the same sender share that sender's limit.

A Redis Lua script uses Redis server time to atomically remove expired reservations, check the rolling-hour cap and minimum spacing, and reserve capacity for an email. The reservation is idempotent by email ID, so parallel workers share one rate-limit decision. Reservations are retained after SMTP failures to avoid releasing capacity while other sends may be in progress.

When capacity is not available, the worker moves the BullMQ job to a future time and retries it. It does not mark the message permanently failed or discard it. Worker concurrency is configured separately with `WORKER_CONCURRENCY`.

If the sender's owner has connected Slack, the worker sends a notification when the hourly cap is reached. Redis deduplicates notifications for the same rate-limit window. If Slack is not connected or Slack configuration is unavailable, email processing continues without a notification.

### Search and queue visibility

Elasticsearch is a search index, not the authoritative data store. Search results are resolved back through PostgreSQL and filtered by the authenticated user's ownership and current status. If Elasticsearch is unavailable, the search endpoint returns an error instead of presenting an unavailable search as an empty result.

Bull Board is mounted at `/admin/queues` and observes the existing email queue. Queue payloads contain email IDs rather than recipient addresses or message bodies.

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Styling | CSS used by the dashboard |
| API | Node.js, TypeScript, Express |
| Database | PostgreSQL, Prisma |
| Queue and shared rate limiting | BullMQ, Redis |
| Search | Elasticsearch |
| Email | Nodemailer, Ethereal SMTP |
| Authentication | Google OAuth 2.0, server-side sessions |
| Notifications | Slack OAuth v2 and `chat.postMessage` |
| Local infrastructure | Docker Compose |

## Application layout

The dashboard uses a left navigation rail for Scheduled and Sent emails, with a primary Compose email action. The workspace shows delivery and sender summary cards above the email queue, while account details and the Slack connection are available in the surrounding workspace controls. The Compose flow brings sender selection, recipients, message content, and scheduling options together.

The codebase is organized as a root npm workspace. The backend API, worker, and Prisma migrations live under `backend/`; the Prisma schema is at `backend/prisma/schema.prisma`. The React/Vite dashboard is a separate workspace, and Docker Compose defines the local data services.

## Getting started

### Prerequisites

- Node.js 20 or newer
- npm
- Docker with Docker Compose
- A Google OAuth web client to use Google sign-in
- An Ethereal test account to send and inspect test email
- A Slack app if you want to exercise Slack notifications

### 1. Configure environment variables

Copy `.env.example` to `.env` in the repository root. Set private values for the secrets and credentials before starting the application. Do not commit `.env` or expose backend secrets through frontend variables.

For email testing, create an account at [Ethereal Email](https://ethereal.email/) and configure its SMTP username and password. Use the host and port shown for that account; the usual defaults are `smtp.ethereal.email` and `587`.

### 2. Start the data services

```powershell
docker compose up -d postgres redis elasticsearch
```

### 3. Install dependencies and prepare the database

```powershell
npm install
npm run db:generate --workspace backend
npm run db:deploy --workspace backend
```

### 4. Start the backend and frontend

Run the backend API and worker in one terminal:

```powershell
npm run dev:backend
```

Run the frontend in a second terminal:

```powershell
npm run dev:frontend
```

The Vite development server proxies `/api` requests to `http://localhost:3000`. The dashboard is available at `http://localhost:5173`, the API health endpoint is `http://localhost:3000/health`, and dependency readiness is reported by `http://localhost:3000/ready`.

For production, route the frontend and `/api` through a same-origin HTTPS reverse proxy or configure an equivalent credentialed setup. The local Vite proxy is for development.

## Environment variables

The backend loads `.env` from the repository root when started through the workspace scripts.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string. |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | Redis connection used by BullMQ and rate limiting. |
| `ELASTICSEARCH_URL`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`, `ELASTICSEARCH_EMAIL_INDEX` | Elasticsearch connection and email index settings. |
| `SESSION_SECRET` | Secret used for session and OAuth-state identifiers; use at least 32 characters. |
| `TOKEN_ENCRYPTION_KEY` | Key material used to derive the AES-256-GCM key for Slack tokens at rest; use at least 32 characters. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Google OAuth web client and callback configuration. |
| `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_REDIRECT_URI` | Slack OAuth app and callback configuration. |
| `SLACK_BOT_TOKEN`, `SLACK_NOTIFICATION_CHANNEL_ID` | Optional development fallback for Slack notifications. |
| `ETHEREAL_HOST`, `ETHEREAL_PORT`, `ETHEREAL_USER`, `ETHEREAL_PASSWORD` | Ethereal SMTP transport settings. |
| `WORKER_CONCURRENCY` | Number of email jobs a worker can process concurrently; default is `5`. |
| `PROCESSING_STALE_AFTER_MS` | Processing lease duration before an uncertain delivery is marked unknown; default is `300000`. |
| `OUTBOX_RETRY_INTERVAL_MS` | Delay between outbox and queue reconciliation retries; default is `5000`. |
| `RATE_LIMIT_REDIS_PREFIX`, `SLACK_RATE_LIMIT_REDIS_PREFIX` | Redis key prefixes for sender reservations and Slack notification deduplication. |
| `MIN_EMAIL_DELAY_MS`, `MAX_EMAILS_PER_HOUR_PER_SENDER` | Defaults used when a sender is created without explicit rate settings; default to `2000` ms and `100`. |
| `FRONTEND_ORIGIN` | OAuth redirect target after authentication; default is `http://localhost:5173`. |

The values in `.env.example` are for local development. Generate private random values for `SESSION_SECRET` and `TOKEN_ENCRYPTION_KEY`. Keep credentials on the backend; never prefix them with `VITE_`.

## OAuth setup

### Google sign-in

Create a Google OAuth 2.0 web application client. Add the callback URL `http://localhost:3000/api/auth/google/callback` as an authorized redirect URI, then set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `.env`.

The backend handles the authorization-code exchange and validates one-time OAuth state. After authentication, the browser receives an opaque HTTP-only session cookie; session tokens are not stored in browser local storage.

### Slack connection

Create a Slack app with OAuth v2 enabled and add `http://localhost:3000/api/auth/slack/callback` as a redirect URI. Configure the Slack client ID, secret, and callback URL in `.env`. A signed-in user can then connect Slack from the dashboard.

The backend stores the user's Slack token encrypted at rest. The status endpoint returns whether Slack is connected, not the token. To see a live notification, connect a Slack workspace, configure a sender with a low hourly limit, schedule enough emails to reach the cap, and check the authorized channel.

## API overview

Application data endpoints require the HTTP-only session cookie. The server determines data ownership from the authenticated session; clients do not supply a `userId`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/auth/google` | Start Google OAuth. |
| `GET` | `/api/auth/me` | Return the current session user. |
| `POST` | `/api/auth/logout` | Revoke the current session. |
| `GET` | `/api/auth/slack` | Start Slack OAuth for the signed-in user. |
| `GET` | `/api/auth/slack/status` | Return the current user's Slack connection status. |
| `GET`, `POST` | `/api/senders` | List or create the current user's senders. |
| `POST` | `/api/campaigns` | Create and schedule a campaign and its recipients (1–10,000 addresses). |
| `GET` | `/api/emails/scheduled?page=1&pageSize=20` | List the user's scheduled email rows. |
| `GET` | `/api/emails/search` | Search user-owned emails with query, status, campaign, sender, and pagination filters. |
| `GET` | `/admin/queues` | View the authenticated Bull Board queue dashboard. |

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

The selected sender owns the rate policy. If legacy rate fields are included in a campaign request, they must match the sender's current settings.

## Dashboard behavior

- **Sign-in and account:** Google OAuth, user profile details, and session logout.
- **Scheduled:** paginated, user-scoped email list with loading and empty states.
- **Sent:** searchable sent and failed messages with status, pagination, and details.
- **Compose:** choose a sender, paste addresses or import a CSV/TXT file, review detected and invalid addresses, enter a subject and body, choose a start time, and schedule the campaign.
- **Sending pace:** shows the selected sender's stored hourly cap and minimum delay.
- **Slack:** connection status is restored after a page reload; successful OAuth returns a short confirmation.
- **Email details:** shows details already available on the user-scoped row. Cancellation is not exposed as a working action because there is no cancellation API.

The interface follows the assignment's [Figma design](https://www.figma.com/design/kOTwGlESjijCYnMgtHfvfU/Outbox-Labs-Assignment?node-id=59-4050&p=f&m=dev). The supplied screenshots show the Google sign-in screen and the scheduled-email workspace.

## Verification

The project provides these root-level checks:

```powershell
npm run typecheck
npm run build
npm test
```

By default, tests that need live PostgreSQL, Redis, and Elasticsearch are skipped. With those services running, enable the integration tests with:

```powershell
$env:RUN_INTEGRATION_TESTS='1'; npm test
```

Validate the Prisma schema after schema changes with:

```powershell
npx prisma validate --schema backend/prisma/schema.prisma
```

The integration suite uses local services and test SMTP stubs. A passing test suite does not verify delivery to a live Slack workspace or Ethereal account; those flows need to be demonstrated separately.

## Known limitations and trade-offs

- SMTP delivery cannot be guaranteed exactly once if a process fails after the provider accepts a message but before the database records success. Such cases are recorded as `DELIVERY_UNKNOWN` for verification.
- Rate reservations remain consumed after SMTP failures to protect the sender cap while concurrent jobs may be active.
- The current SMTP configuration uses one Ethereal account for authentication. Sender records control the visible From name and address; they do not represent separate SMTP credentials.
- The dashboard does not cancel queued email. A safe cancellation flow needs an authenticated API and coordinated database and queue state changes.
- Slack notifications require a connected Slack account or configured development fallback. Missing Slack configuration does not stop email processing.

## Assignment demo checklist

The assignment asks for a demo video of no more than five minutes. The video should show scheduling an email, the Scheduled and Sent views, and a restart scenario where a future email still sends after the service starts again. A brief rate-limit demonstration is optional. Add the recording to the submission separately; it is not included in this README.

The assignment also asks submitters to note assumptions and trade-offs. The behavior and limitations above document the main ones for this implementation.


