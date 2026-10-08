# 📦 Inventory Management System

A full-stack web application for managing product inventory. Users can add, search, update and delete products, and get automatic low-stock alerts, all without page reloads.

## Features

- Add products with ID, name, category, quantity and price
- Live search by product ID, name or category
- Increase or decrease stock with +1 / −1 buttons
- Edit quantity and price
- Delete products with confirmation
- Low-stock alert banner and highlighted rows (quantity of 5 or below)
- Input validation in three layers: HTML, Flask and SQLite `CHECK` constraints
- Stock cannot go below zero
- Friendly error messages (duplicate ID, product not found, server unreachable)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (Fetch API) |
| Tooling | Node.js, npm, live-server |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite |

## Architecture

```
Browser (HTML/CSS/JS, port 5500)
   → Fetch API (JSON) →
Flask REST API (port 5000)
   → SQL →
SQLite (inventory.db)
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/products?q=` | List and search products |
| GET | `/api/products/low-stock` | Products with low stock |
| POST | `/api/products` | Add a product |
| PUT | `/api/products/<id>` | Update quantity and price |
| PATCH | `/api/products/<id>/stock` | Increase or decrease stock |
| DELETE | `/api/products/<id>` | Delete a product |

## Database Schema

```sql
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL,
    quantity   INTEGER NOT NULL CHECK (quantity >= 0),
    price      REAL NOT NULL CHECK (price >= 0),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Setup and Run

**Prerequisites:** Python 3.10+ and Node.js

**1. Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**2. Frontend** (second terminal, from the project root)
```bash
npm install
npm run dev
```

**3. Open** http://localhost:5500

## Edge Cases Tested

- Searching for a product that doesn't exist
- Reducing stock below zero
- Negative quantity or price
- Duplicate product ID
- Non-numeric input
- Backend server not running

## Possible Future Improvements

- User login and roles
- Stock movement history
- CSV export and dashboard
- Per-product reorder levels
- PostgreSQL and cloud deployment
