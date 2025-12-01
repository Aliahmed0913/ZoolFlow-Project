#  StackPay – Basic Payment Integration Project

A Django REST Framework project that demonstrates a simple payment integration workflow with **PayMob**, user registration, notifications, and Celery background tasks.

---

##  Features

### User App
- Handles **user registration** and authentication.
- A **Django signal** triggers the Notification app when a new user is created.

### Notification App
- Sends an **email code** to newly registered users.
- Integrates with **Celery** to remove used email codes from the database asynchronously.

### Customer App
- Manages customer profiles and addresses.
- Provides local currency resolution based on country.

### Transactions App
- **Transaction API**: Create and list customer transactions.
- **Webhook API**: Receives PayMob callbacks, verifies HMAC, and updates transaction status.
- **Transaction View**: Simple HTML page for testing payment flow.
- **Pagination & Filtering**: Paginated transaction listing with filters on status and creation date.
- **Services Layer**:
  - `PayMob` client with retry logic and caching.
  - `create_transaction` orchestration for DB + PayMob order creation.
  - Webhook service for secure HMAC verification and transaction updates.

### Background Tasks
- **Celery worker** removes used email codes from the database automatically.

---

## Tech Stack
- **Django** + **Django REST Framework**
- **Celery** + **Redis** (for async tasks)
- **PayMob API** integration
- **pytest** for testing
- **PostgreSQL/MySQL/SQLite** (choose your DB)

---

## Running Locally

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/stackpay.git
   cd stackpay

2. Install dependencies: 
pip install -r requirements.txt

3. - Set environment variables in .env:
PAYMOB_API_KEY=your_api_key
PAYMOB_PAYMENT_KEY=your_payment_key
SECRET_KEY=your_django_secret

4. run migrations
5. - Start Celery worker:
celery -A stackpay worker -l info expired,celery
