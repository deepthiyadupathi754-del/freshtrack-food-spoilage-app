"""SQLite storage and inventory operations for FreshTrack."""
from __future__ import annotations

import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any


DB_PATH = Path(os.environ.get("FRESHTRACK_DB", Path(__file__).with_name("freshtrack.db")))


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    """Create missing tables; existing inventory records are left intact."""
    with connect(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            quantity REAL NOT NULL CHECK(quantity >= 0),
            unit TEXT NOT NULL,
            reorder_level REAL NOT NULL DEFAULT 0 CHECK(reorder_level >= 0),
            expiry_date TEXT NOT NULL,
            supplier TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            change REAL NOT NULL,
            reason TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            sold_on TEXT NOT NULL,
            quantity REAL NOT NULL CHECK(quantity >= 0),
            UNIQUE(item_id, sold_on)
        );
        CREATE INDEX IF NOT EXISTS idx_items_expiry ON items(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_movements_item ON stock_movements(item_id);
        """)


def add_item(data: dict[str, Any], db_path: str | Path | None = None) -> int:
    required = ("name", "category", "location", "unit", "expiry_date")
    if any(not str(data.get(k, "")).strip() for k in required):
        raise ValueError("Please complete all required item fields.")
    quantity, reorder = float(data["quantity"]), float(data["reorder_level"])
    if quantity < 0 or reorder < 0:
        raise ValueError("Quantity and reorder level cannot be negative.")
    date.fromisoformat(str(data["expiry_date"]))
    with connect(db_path) as conn:
        cur = conn.execute("""INSERT INTO items
          (name,category,location,quantity,unit,reorder_level,expiry_date,supplier)
          VALUES (?,?,?,?,?,?,?,?)""", (str(data["name"]).strip(), str(data["category"]).strip(),
          str(data["location"]).strip(), quantity, str(data["unit"]).strip(), reorder,
          str(data["expiry_date"]), str(data.get("supplier", "")).strip()))
        item_id = int(cur.lastrowid)
        if quantity:
            conn.execute("INSERT INTO stock_movements(item_id,change,reason,note) VALUES(?,?,?,?)",
                         (item_id, quantity, "Opening stock", "Initial quantity"))
        return item_id


def list_items(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM items ORDER BY expiry_date, name")]


def update_stock(item_id: int, change: float, reason: str, note: str = "", db_path: str | Path | None = None) -> None:
    change = float(change)
    if change == 0:
        raise ValueError("Stock change must be greater than zero or less than zero.")
    with connect(db_path) as conn:
        row = conn.execute("SELECT quantity FROM items WHERE id=?", (item_id,)).fetchone()
        if row is None:
            raise ValueError("Inventory item was not found.")
        new_quantity = float(row["quantity"]) + change
        if new_quantity < 0:
            raise ValueError("This adjustment would make stock negative.")
        conn.execute("UPDATE items SET quantity=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_quantity, item_id))
        conn.execute("INSERT INTO stock_movements(item_id,change,reason,note) VALUES(?,?,?,?)",
                     (item_id, change, reason.strip() or "Adjustment", note.strip()))


def record_sales(item_id: int, sold_on: str, quantity: float, db_path: str | Path | None = None) -> None:
    date.fromisoformat(sold_on)
    quantity = float(quantity)
    if quantity < 0:
        raise ValueError("Sales quantity cannot be negative.")
    with connect(db_path) as conn:
        if conn.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone() is None:
            raise ValueError("Inventory item was not found.")
        conn.execute("INSERT INTO sales_history(item_id,sold_on,quantity) VALUES(?,?,?) "
                     "ON CONFLICT(item_id,sold_on) DO UPDATE SET quantity=excluded.quantity",
                     (item_id, sold_on, quantity))


def sales_summary(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("""SELECT i.id, i.name, i.unit, i.quantity,
          COALESCE(SUM(CASE WHEN s.sold_on >= date('now','-7 day') THEN s.quantity END),0) AS sold_7d,
          COUNT(s.id) AS recorded_days
          FROM items i LEFT JOIN sales_history s ON s.item_id=i.id GROUP BY i.id ORDER BY i.name""")
        result = []
        for r in rows:
            d = dict(r)
            d["daily_average"] = d["sold_7d"] / 7
            d["days_of_stock"] = d["quantity"] / d["daily_average"] if d["daily_average"] else None
            result.append(d)
        return result


def get_movements(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute("""SELECT m.*,i.name,i.unit FROM stock_movements m
            JOIN items i ON i.id=m.item_id ORDER BY m.created_at DESC,m.id DESC LIMIT 200""")]
