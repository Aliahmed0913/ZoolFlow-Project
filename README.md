#  ZoolFlow – Basic Payment Integration Project

A Django REST Framework project that demonstrates a simple payment integration workflow with **PayMob**, user registration, notifications, and Celery background tasks.

---

##  Features

### User App
- **User Registration**
  - Provides an endpoint for new user sign‑up with validation and throttling (`sign_up` scope).
  - When a user is successfully created, an **Email Code object** is automatically generated and tied to the Notification app.

- **User Profile Management**
  - View and update user profiles (`GET`, `PATCH`).
  - Role‑based permissions:
    - **Admin/Staff** can list and retrieve all profiles.
    - **Admin** can partially update other users.
    - **Owner** can access and edit their own profile.
  - Custom actions:
    - `mine`: view or update the authenticated user’s profile.
    - `mine/new-password`: securely change the authenticated user’s password.

- **Email Verification**
  - `validate`: verify a user’s email code and issue JWT tokens (`refresh` + `access`).
  - `resend`: resend a new verification code if expired or invalid.
  - Throttling applied to verification and resend actions.

- **Authentication**
  - Custom JWT login view (`CustomTokenObtainPairView`) with request throttling (`login` scope).
  - Limits login attempts to 10 per minute for security.


### Customer App
- **Customer Profile**
  - Provides endpoints to **retrieve, update, or delete** the authenticated user’s customer profile.
  - Strong validation ensures data integrity and ties each profile directly to its user account.

- **Customer Addresses**
  - Full CRUD support for customer addresses via a `ModelViewSet`.
  - Each user can only access and manage addresses linked to their own profile.
  - Enforces a maximum number of addresses (`ADDRESSES_COUNT`) to prevent misuse.

- **Know Your Customer (KYC)**
  - Endpoints to retrieve and update KYC information for the authenticated customer.
  - Validates identity documents and tracks review status.
  - Ensures **only one KYC record per customer** for compliance.

- **Admin Interface**
  - Custom admin forms with inline editing:
    - **AddressInline**: manage customer addresses directly from the Customer admin page.
    - **KYCInline**: manage KYC records with restricted fields (document details are read‑only).
  - Admin restrictions:
    - Cannot create new customers directly.
    - Cannot delete customers from the admin panel.
  - Provides a clear overview with list display (`id`, name, email, verification status, created date).

### Transactions App
- **Transaction API**: Create and list customer transactions.
- **Webhook API**: Receives PayMob callbacks, verifies HMAC, and updates transaction status.
- **Transaction View**: Simple HTML page for testing payment flow.
- **Pagination & Filtering**: Paginated transaction listing with filters on status and creation date.
- **Services Layer**:
  - `PayMob` client with retry logic and caching.
  - `create_transaction` orchestration for DB + PayMob order creation.
  - Webhook service for secure HMAC verification and transaction updates.

### Notification App
- The notification proccess also done in background with **Celery worker**
- A **Django signal** triggers the Notification app when a new email code is created.
- Sends an **email code** to newly registered users with welcome message.

### Background Tasks
- **Celery workers** handle user notifications and remove used email codes from the database automatically

## Tech Stack
- **Django** + **Django REST Framework**
- **Celery** + **Redis** (for async tasks)
- **PayMob API** integration
- **pytest** for testing
- **MySQL**

---

## Running Locally

1. Clone the repo:
   ```bash
   git clone https://github.com/Aliahmed0913/stackpay.git
   cd stackpay

2. Set your environment variables in .env:
    ```bash
    SECRET_KEY=your_SECRET_KEY
    DATABASE_URL=your_DATABASE_URL
    MYSQL_DATABASE=your_MYSQL_DATABASE
    MYSQL_USER=your_MYSQL_USER
    MYSQL_PASSWORD=your_MYSQL_PASSWORD
    MYSQL_ROOT_PASSWORD=your_MYSQL_ROOT_PASSWORD
    EMAIL_HOST_USER=your_EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD=your_EMAIL_HOST_PASSWORD
    DEFAULT_FROM_EMAIL=your_DEFAULT_FROM_EMAIL
    PAYMOB_API_KEY=your_PAYMOB_API_KEY
    AUTH_PAYMOB_TOKEN=your_AUTH_PAYMOB_TOKEN
    PAYMOB_AUTH_CACH_KEY=your_PAYMOB_AUTH_CACH_KEY
    ORDER_PAYMOB_URL=your_ORDER_PAYMOB_URL
    PAYMOB_PAYMENT_URL_KEY=your_PAYMOB_PAYMENT_URL_KEY
    PAYMOB_PAYMENT_KEY=your_PAYMOB_PAYMENT_KEY
    CELERY_BROKER_URL=your_CELERY_BROKER_URL
    CELERY_TIMEZONE=your_CELERY_TIMEZONE
    NGROK_AUTHTOKEN=your_NGROK_AUTHTOKEN

3. Build and run dockerfile with docker compose: 
    ```bash
    docker compose up --build -d

4. Access application from ngrok dashboard:
    ```bash
    http://localhost:4040