# ZoolFlow

ZoolFlow is a Django REST Framework backend for:
- user registration and email verification
- customer profile + KYC management
- payment transaction orchestration with PayMob
- webhook-driven notification tracking
- background jobs with Celery

## Tech Stack
- Python 3.11
- Django 5
- Django REST Framework
- Celery + Redis
- PostgreSQL (via `DATABASE_URL`)
- MinIO/S3 storage for KYC documents
- pytest + pytest-django

## Project Apps
- `zoolflow.users`: auth, signup, verification code flow, profile endpoints
- `zoolflow.customers`: customer profile, addresses, KYC domain
- `zoolflow.transactions`: transaction creation/listing, PayMob orchestration, webhook endpoint
- `zoolflow.notifications`: mail/webhook event tracking + async tasks

## API Base
- `/api/v1/users/`
- `/api/v1/customers/`
- `/api/v1/transactions/`
- `/api/v1/notifications/`

## Requirements
- Python 3.11+
- Docker + Docker Compose (optional, but recommended)
- Redis
- PostgreSQL

## Environment Variables
Create a `.env` file in project root. At minimum, configure:

### Core Django
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` (example: `postgres://user:pass@db:5432/zoolflow`)

### Cache / Celery
- `REDIS_URL_CACHE`
- `CELERY_BROKER_URL`
- `CELERY_TIMEZONE`

### Mailgun
- `MAILGUN_API_KEY`
- `EMAIL_DOMAIN`
- `MAILGUN_WEBHOOK_SIGINING_KEY`

### PayMob
- `PAYMOB_API_KEY`
- `AUTH_PAYMOB_TOKEN`
- `ORDER_PAYMOB_URL`
- `PAYMOB_PAYMENT_URL_KEY`
- `PAYMOB_PAYMENT_KEY`
- `HMAC_SECRET_KEY`

### S3/MinIO for KYC files
- `BUCKET_NAME`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_ENDPOINT_URL`

### Optional
- `NGROK_AUTHTOKEN`

## Run With Docker
```bash
docker compose up --build
```

App services:
- API: `http://localhost:8000`
- ngrok dashboard: `http://localhost:4040`
- MinIO API: `http://localhost:9000`
- MinIO console: `http://localhost:9001`

## Run Locally (without Docker)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

Run worker:
```bash
celery -A config worker -l info -Q celery,expired
```

Run beat:
```bash
celery -A config beat -l info
```

## Testing
Run full test suite:
```bash
pytest
```

Run only transactions tests:
```bash
pytest zoolflow/transactions/tests -q
```

## Notes
- Transactions are provider-backed (PayMob). For local development/tests, external calls should be mocked.
- KYC files use S3-compatible storage (`django-storages` + MinIO/S3 endpoint).
