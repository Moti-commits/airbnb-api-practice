from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB = "airbnb.db"


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def setup():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, location TEXT, price REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER, guest TEXT,
        check_in TEXT, check_out TEXT)""")
    conn.commit()
    conn.close()


@app.post("/listings")
def add_listing():
    d = request.json
    conn = db()
    cur = conn.execute(
        "INSERT INTO listings (title, location, price) VALUES (?, ?, ?)",
        (d["title"], d["location"], d["price"]))
    conn.commit()
    return jsonify({"id": cur.lastrowid}), 201


@app.get("/listings")
def get_listings():
    location = request.args.get("location")
    conn = db()
    if location:
        rows = conn.execute(
            "SELECT * FROM listings WHERE location = ?", (location,))
    else:
        rows = conn.execute("SELECT * FROM listings")
    return jsonify([dict(r) for r in rows])


@app.post("/bookings")
def book():
    d = request.json
    conn = db()
    # Block double booking: dates must not overlap an existing booking
    clash = conn.execute(
        """SELECT 1 FROM bookings WHERE listing_id = ?
           AND check_in < ? AND check_out > ?""",
        (d["listing_id"], d["check_out"], d["check_in"])).fetchone()
    if clash:
        return jsonify({"error": "Dates already booked"}), 409
    cur = conn.execute(
        "INSERT INTO bookings (listing_id, guest, check_in, check_out) "
        "VALUES (?, ?, ?, ?)",
        (d["listing_id"], d["guest"], d["check_in"], d["check_out"]))
    conn.commit()
    return jsonify({"id": cur.lastrowid}), 201


if __name__ == "__main__":
    setup()
    app.run(debug=True)
