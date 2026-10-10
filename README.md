# Rakshana2.O

Backend/API-only integration stage for the Rakshana cyber-safety service. The UI will be wired in a later stage. `frontend/api.js` is included as the client module for that integration.

## Deploy the API

Deploy from the repository root using the included `Procfile`. The service runs `backend/run.py` with Gunicorn and listens on the platform-provided `PORT`. Dependencies are listed in root `requirements.txt`.

Provision PostgreSQL and Redis, then set these required environment variables in the hosting provider; never commit real values:

- `FLASK_ENV=production`
- `SECRET_KEY` — long, random Flask secret
- `JWT_SECRET_KEY` — separate, long, random JWT signing secret
- `DATABASE_URL` — PostgreSQL connection URL
- `ENCRYPTION_KEY` — exactly 32 characters
- `REDIS_URL` — Redis connection URL (used by rate limiting and Celery)
- `CORS_ORIGINS` — comma-separated allowed frontend origins; set this when the UI is deployed

`backend/.env.example` is a safe local template. Copy it to `backend/.env`, replace placeholders, and do not use the sample keys in production. `.env` is ignored by Git.

Health check: `/api/health`. API routes are under `/api`; the client uses the same-origin `/api` path by default. Configure the client base URL if the API and future UI are hosted separately.
