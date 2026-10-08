import sqlite3
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# ---------- 1. App setup ----------
app = Flask(__name__)
CORS(app)
DB = "inventory.db"
LOW_STOCK_LIMIT = 5

# ---------- 2. Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                category   TEXT NOT NULL,
                quantity   INTEGER NOT NULL CHECK (quantity >= 0),
                price      REAL    NOT NULL CHECK (price >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""")

# ---------- 3. Validation helpers ----------
def parse_num(value, cast, field):
    try:
        n = cast(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a valid {'whole ' if cast is int else ''}number")
    if n < 0:
        raise ValueError(f"{field} cannot be negative")
    return n

def error(msg, code=400):
    return jsonify({"error": msg}), code

# ---------- 4. Routes ----------
# READ + SEARCH
@app.route("/api/products", methods=["GET"])
def list_products():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        rows = db.execute(
            """SELECT * FROM products
               WHERE product_id LIKE ? OR name LIKE ? OR category LIKE ?
               ORDER BY name""", (like, like, like)).fetchall()
    else:
        rows = db.execute("SELECT * FROM products ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

# LOW STOCK
@app.route("/api/products/low-stock", methods=["GET"])
def low_stock():
    rows = get_db().execute(
        "SELECT * FROM products WHERE quantity <= ? ORDER BY quantity",
        (LOW_STOCK_LIMIT,)).fetchall()
    return jsonify([dict(r) for r in rows])

# CREATE
@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True) or {}
    pid = str(data.get("product_id", "")).strip()
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    if not pid or not name or not category:
        return error("Product ID, name and category are required")
    try:
        qty = parse_num(data.get("quantity"), int, "Quantity")
        price = parse_num(data.get("price"), float, "Price")
    except ValueError as e:
        return error(str(e))
    try:
        db = get_db()
        db.execute("INSERT INTO products (product_id, name, category, quantity, price) "
                   "VALUES (?,?,?,?,?)", (pid, name, category, qty, price))
        db.commit()
    except sqlite3.IntegrityError:
        return error(f"Product ID '{pid}' already exists", 409)
    print(f"[ADDED] ID={pid} | Name={name} | Category={category} | Qty={qty} | Price={price}", flush=True)
    return jsonify({"message": "Product added"}), 201
# UPDATE (set quantity / price)
@app.route("/api/products/<pid>", methods=["PUT"])
def update_product(pid):
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE product_id=?", (pid,)).fetchone()
    if not row:
        return error("Product not found", 404)
    try:
        qty = parse_num(data["quantity"], int, "Quantity") if "quantity" in data else row["quantity"]
        price = parse_num(data["price"], float, "Price") if "price" in data else row["price"]
    except ValueError as e:
        return error(str(e))
    db.execute("UPDATE products SET quantity=?, price=? WHERE product_id=?", (qty, price, pid))
    db.commit()
    return jsonify({"message": "Product updated"})

# UPDATE (add/remove stock)
@app.route("/api/products/<pid>/stock", methods=["PATCH"])
def adjust_stock(pid):
    data = request.get_json(silent=True) or {}
    try:
        change = int(data.get("change"))
    except (TypeError, ValueError):
        return error("Change must be a whole number")
    db = get_db()
    row = db.execute("SELECT quantity FROM products WHERE product_id=?", (pid,)).fetchone()
    if not row:
        return error("Product not found", 404)
    new_qty = row["quantity"] + change
    if new_qty < 0:
        return error(f"Insufficient stock: only {row['quantity']} available")
    db.execute("UPDATE products SET quantity=? WHERE product_id=?", (new_qty, pid))
    db.commit()
    return jsonify({"message": "Stock updated", "quantity": new_qty})

# DELETE
@app.route("/api/products/<pid>", methods=["DELETE"])
def delete_product(pid):
    db = get_db()
    cur = db.execute("DELETE FROM products WHERE product_id=?", (pid,))
    db.commit()
    if cur.rowcount == 0:
        return error("Product not found", 404)
    return jsonify({"message": "Product deleted"})

# ---------- 5. Start the server ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)