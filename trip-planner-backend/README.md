# Trip Planner API

A Python (FastAPI) backend for the AI Trip Planner mobile app. The mobile
frontend — a separate Expo React Native app — talks to this API over HTTP and
never touches the database directly. The only contract between the two repos
is the HTTP API documented below.

## Stack

- FastAPI + Uvicorn
- Supabase (PostgreSQL) via the `supabase` Python package
- Supabase Auth (email + password) with JWT verification on every protected route

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Copy `.env.example` to `.env` and fill in the values. All configuration comes
from environment variables — nothing is hardcoded.

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon (public) key — used for auth flows |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key — server-side only, e.g. creating profile rows at sign-up |
| `SUPABASE_JWT_SECRET` | Secret used to verify user JWTs (Project Settings -> API -> JWT Settings) |
| `ALLOWED_ORIGINS` | Comma-separated list of origins allowed by CORS (Expo dev ports + your deployed frontend domain) |
| `API_PORT` | Port the API listens on (default `8000`) |

## Run

```bash
uvicorn app.main:app --reload
```

The API is then available at `http://localhost:8000`. Interactive, auto-generated
API docs are served by FastAPI for free at [`/docs`](http://localhost:8000/docs) —
open it in a browser to explore and try every endpoint.

## Endpoints

### Health

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/health` | none | Returns `{ "status": "ok" }` |

### Auth — `/api/auth`

| Method | Path | Auth | Body | Description |
| --- | --- | --- | --- | --- |
| POST | `/api/auth/sign-up` | none | `{ email, password, full_name }` | Creates the account + profile row, returns `{ session: { access_token, refresh_token, expires_in }, profile, error }` |
| POST | `/api/auth/sign-in` | none | `{ email, password }` | Signs in, same response shape as sign-up |
| POST | `/api/auth/refresh` | none | `{ refresh_token }` | Exchanges a refresh token for a new session |

Errors are returned as `{ "error": "message" }` — never raw stack traces.

### Trips — `/api/trips`

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/trips` | Bearer token | The signed-in user's trips, newest first |
| POST | `/api/trips` | Bearer token | Create a trip (destination required, dates `YYYY-MM-DD`, status defaults to `Planning`) |
| GET | `/api/trips/{id}` | Bearer token | One trip; `404` if not found or not owned |
| PATCH | `/api/trips/{id}` | Bearer token | Update allowed fields only |
| DELETE | `/api/trips/{id}` | Bearer token | `204` on success |
| GET | `/api/trips/{id}/itinerary` | Bearer token | Itinerary items ordered by `day_number` |

> **Every trips/itinerary route requires the header
> `Authorization: Bearer <access_token>`** (the token from sign-up / sign-in /
> refresh). Invalid or expired tokens are rejected with `401 { "error": ... }`.

## Data model

- `profiles` — one row per user (`id` matches the auth user): email, full name, avatar.
- `trips` — user's trips: title, destination, source, start/end dates, budget,
  interests (text array), travelers, description, status (`Planning` / `Upcoming` /
  `Completed`), cover image path.
- `trip_itinerary_items` — day-by-day plan attached to a trip: day number, title,
  category (`flight` / `hotel` / `car` / `activity` / `meal` / `extra`), start
  time, description, and a free-form `metadata` JSON field.

Row Level Security is enabled on every table: users can only read and write
rows they own (ownership checked with `auth.uid()`). Itinerary items are
scoped through their parent trip.

## CORS

`CORSMiddleware` allows the origins listed in `ALLOWED_ORIGINS`. For Expo
development the defaults include the common localhost ports (19000–19002,
8081, 3000); add your deployed frontend domain before going live.

## Project structure

```
trip-planner-backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, error handlers
│   ├── core/
│   │   ├── config.py      # Environment-variable settings
│   │   ├── database.py    # Supabase clients (anon + service role)
│   │   ├── deps.py        # JWT verification dependency
│   │   └── errors.py      # Consistent { "error": ... } responses
│   ├── routers/
│   │   ├── auth.py        # /api/auth/*
│   │   ├── trips.py       # /api/trips/*
│   │   └── health.py      # /api/health
│   └── schemas/
│       ├── auth.py        # Auth request/response models
│       └── trips.py       # Trip / itinerary request + response models
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
