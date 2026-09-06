from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DATABASE = "garage_dost.db"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# CREATE DATABASE
# -----------------------------

def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS mechanics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            online INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            vehicle_type TEXT,
            vehicle_number TEXT,
            problem TEXT,
            latitude REAL,
            longitude REAL,
            mechanic_id INTEGER,
            status TEXT DEFAULT 'Searching'
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# HOME
# -----------------------------

@app.route("/")
def home():
    return "🚗 Garage Dost Backend is Running!"


# -----------------------------
# CUSTOMER REGISTER
# -----------------------------

@app.route("/customer/register", methods=["POST"])
def customer_register():

    data = request.json

    name = data.get("name")
    phone = data.get("phone")
    password = data.get("password")

    if not name or not phone or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    conn = get_db()

    conn.execute("""
        INSERT INTO customers
        (name, phone, password)
        VALUES (?, ?, ?)
    """, (name, phone, password))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Customer registered successfully"
    })


# -----------------------------
# CUSTOMER LOGIN
# -----------------------------

@app.route("/customer/login", methods=["POST"])
def customer_login():

    data = request.json

    phone = data.get("phone")
    password = data.get("password")

    conn = get_db()

    customer = conn.execute("""
        SELECT * FROM customers
        WHERE phone = ? AND password = ?
    """, (phone, password)).fetchone()

    conn.close()

    if customer:

        return jsonify({
            "success": True,
            "message": "Login successful",
            "customer_id": customer["id"],
            "name": customer["name"]
        })

    return jsonify({
        "success": False,
        "message": "Invalid phone number or password"
    }), 401


# -----------------------------
# MECHANIC REGISTER
# -----------------------------

@app.route("/mechanic/register", methods=["POST"])
def mechanic_register():

    data = request.json

    name = data.get("name")
    phone = data.get("phone")
    password = data.get("password")

    conn = get_db()

    conn.execute("""
        INSERT INTO mechanics
        (name, phone, password)
        VALUES (?, ?, ?)
    """, (name, phone, password))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Mechanic registered successfully"
    })


# -----------------------------
# MECHANIC LOGIN
# -----------------------------

@app.route("/mechanic/login", methods=["POST"])
def mechanic_login():

    data = request.json

    phone = data.get("phone")
    password = data.get("password")

    conn = get_db()

    mechanic = conn.execute("""
        SELECT * FROM mechanics
        WHERE phone = ? AND password = ?
    """, (phone, password)).fetchone()

    conn.close()

    if mechanic:

        return jsonify({
            "success": True,
            "message": "Mechanic login successful",
            "mechanic_id": mechanic["id"],
            "name": mechanic["name"]
        })

    return jsonify({
        "success": False,
        "message": "Invalid login details"
    }), 401


# -----------------------------
# MECHANIC GO ONLINE
# -----------------------------

@app.route("/mechanic/online", methods=["POST"])
def mechanic_online():

    data = request.json

    mechanic_id = data.get("mechanic_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    conn = get_db()

    conn.execute("""
        UPDATE mechanics
        SET online = 1,
            latitude = ?,
            longitude = ?
        WHERE id = ?
    """, (latitude, longitude, mechanic_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Mechanic is now ONLINE 🟢"
    })


# -----------------------------
# CREATE SERVICE REQUEST
# -----------------------------

@app.route("/service/request", methods=["POST"])
def create_service_request():

    data = request.json

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO service_requests
        (
            customer_name,
            customer_phone,
            vehicle_type,
            vehicle_number,
            problem,
            latitude,
            longitude,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("customer_name"),
        data.get("customer_phone"),
        data.get("vehicle_type"),
        data.get("vehicle_number"),
        data.get("problem"),
        data.get("latitude"),
        data.get("longitude"),
        "Searching"
    ))

    request_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Mechanic request created 🚨",
        "request_id": request_id
    })


# -----------------------------
# GET SERVICE REQUESTS
# -----------------------------

@app.route("/service/requests", methods=["GET"])
def get_service_requests():

    conn = get_db()

    requests = conn.execute("""
        SELECT *
        FROM service_requests
        WHERE status = 'Searching'
    """).fetchall()

    conn.close()

    result = []

    for r in requests:

        result.append({
            "id": r["id"],
            "customer_name": r["customer_name"],
            "customer_phone": r["customer_phone"],
            "vehicle_type": r["vehicle_type"],
            "vehicle_number": r["vehicle_number"],
            "problem": r["problem"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "status": r["status"]
        })

    return jsonify(result)


# -----------------------------
# ACCEPT REQUEST
# -----------------------------

@app.route("/service/accept", methods=["POST"])
def accept_request():

    data = request.json

    request_id = data.get("request_id")
    mechanic_id = data.get("mechanic_id")

    conn = get_db()

    conn.execute("""
        UPDATE service_requests
        SET mechanic_id = ?,
            status = 'Mechanic Accepted'
        WHERE id = ?
    """, (mechanic_id, request_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Request accepted ✅"
    })


# -----------------------------
# UPDATE SERVICE STATUS
# -----------------------------

@app.route("/service/status", methods=["POST"])
def update_status():

    data = request.json

    request_id = data.get("request_id")
    status = data.get("status")

    conn = get_db()

    conn.execute("""
        UPDATE service_requests
        SET status = ?
        WHERE id = ?
    """, (status, request_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Status updated",
        "status": status
    })


# -----------------------------
# RUN SERVER
# -----------------------------

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
