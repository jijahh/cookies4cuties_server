# Cookies4Cuties API 🍪✨

A robust, asynchronous backend API built with **FastAPI** and **Supabase** designed to manage online ordering, product catalogs, administrative workflows, and secure image uploads for a boutique bakery.

🔗 **Live API**: [https://cookies4cuties-server.vercel.app/](https://cookies4cuties-server.vercel.app/)  
📖 **Interactive Docs**: [https://cookies4cuties-server.vercel.app/docs](https://cookies4cuties-server.vercel.app/docs)

---

## 🌟 Overview & Portfolio Highlights

This backend service powers the ordering pipeline for **Cookies4Cuties**. It handles multi-format form submissions, image storage rollbacks on failure, complex order filtering, and secure admin operations.

### Technical Highlights
* **Asynchronous Lifespan Management**: Centralized initialization and clean shared client state management using FastAPI's modern `@asynccontextmanager` pattern.
* **Transactional File Rollbacks**: Automatic cleanup logic that deletes uploaded payment proofs or product assets from Supabase Storage if the subsequent database write fails.
* **Granular Admin Query Engine**: Flexible API parameters supporting multi-field filtering (status, location, date ranges, total price range), dynamic sorting with strict regex pattern matching, and SQL-style range pagination.
* **Timing-Attack Resistant Auth**: Constant-time key verification via Python's `secrets.compare_digest` for secure admin operations.
* **Input Validation & Sanitization**: Strict runtime checks on JSON structures, email formats, payload size boundaries, and file MIME types (`JPEG`, `PNG`, `WebP`).

---

## 🛠️ Tech Stack

* **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
* **Database & Object Storage**: [Supabase](https://supabase.com/) (PostgreSQL + Supabase Storage)
* **Configuration Management**: [Pydantic v2 / pydantic-settings](https://docs.pydantic.dev/)
* **Deployment & Hosting**: [Vercel Serverless](https://vercel.com/)
* **ASGI Server**: Uvicorn

---

## 📂 Project Architecture

```text
cookies4cuties_server/
├── main.py            # Application startup, middleware setup, router integration
├── routes.py          # API route definitions (Order processing & Admin endpoints)
├── config.py          # Environment settings with Pydantic caching (@lru_cache)
├── auth.py            # Authentication dependencies & security enforcement
└── supabase_client.py # Shared Supabase dependency injection setup
```

---

## 🔌 API Reference

### 1. Customer Endpoints

#### `POST /orders`
Creates a new customer order and optionally uploads proof of payment.

* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  * `email` *(string, required)*: Customer email address.
  * `phone_number` *(string, required)*: Customer contact number.
  * `items` *(JSON string, required)*: Array of items, e.g., `[{"product_id": 1, "quantity": 2}]`.
  * `total_price` *(decimal, required)*: Total order price (> 0).
  * `pickup_location` *(string, required)*: Allowed values: `pampanga`, `katipunan`, `rockwell`.
  * `payment_method` *(string, required)*: Allowed values: `cash_on_pickup`, `cash_on_delivery`, `online`.
  * `proof_of_payment` *(file, optional)*: Image file (required for `online` payment method; max 5 MB).

---

### 2. Admin Endpoints

> 🔐 **Authentication required**: Pass your admin secret key via the header `X-Admin-Key: <YOUR_ADMIN_KEY>`.

#### `GET /admin/orders`
Fetch order records with advanced filtering, sorting, and pagination.

* **Query Parameters**:
  * `order_status` *(string, optional)*: Filter by order status (e.g., `pending`).
  * `payment_method` *(string, optional)*: Filter by payment method.
  * `payment_verified` *(boolean, optional)*: Filter by payment verification status.
  * `email` *(string, optional)*: Partial search by email (case-insensitive).
  * `pickup_location` *(string, optional)*: Filter by location.
  * `created_from` / `created_to` *(ISO datetime, optional)*: Date range filter.
  * `min_total` / `max_total` *(decimal, optional)*: Price range filter.
  * `sort_by` *(string)*: Sort field (`created_at`, `total_price`, `order_status`, etc. Default: `created_at`).
  * `sort_order` *(string)*: `asc` or `desc` (Default: `desc`).
  * `limit` *(int)*: Items per page (Default: `50`, Max: `200`).
  * `offset` *(int)*: Pagination offset (Default: `0`).

#### `POST /admin/products`
Add a new product to the catalog with an optional image upload.

* **Content-Type**: `multipart/form-data`
* **Form Parameters**:
  * `product_name` *(string, required)*: Name of the product (1-120 chars).
  * `unit_price` *(decimal, required)*: Unit price (> 0).
  * `product_details` *(string, optional)*: Product description.
  * `active` *(boolean, optional)*: Availability state (Default: `true`).
  * `image` *(file, optional)*: Product image asset.

---

## ⚙️ Local Development Setup

### Prerequisites

* Python **3.10+**
* A Supabase project with an active database table setup and a public/private storage bucket.

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-username/cookies4cuties-server.git
cd cookies4cuties-server

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key
SUPABASE_STORAGE_BUCKET=payment-proofs
MAX_UPLOAD_SIZE_MB=5
ADMIN_API_KEY=your-secure-admin-api-key
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
```

### 4. Run Server

```bash
uvicorn cookies4cuties_server.main:app --reload
```

Access the local server at `http://localhost:8000` and docs at `http://localhost:8000/docs`.

---

## 🛡️ Security & Reliability Features

1. **Storage Orphan Prevention**: When file uploads succeed but database transactions fail, background cleanup handlers attempt immediate removal of the orphaned asset from storage.
2. **Safe Key Verification**: Admin authentication uses cryptographic constant-time string comparisons to guard against timing attacks.
3. **Strict Validation Protocols**: MIME type headers are checked against exact standard definitions, and multi-file payloads are validated before processing to prevent partial batch corruptions.