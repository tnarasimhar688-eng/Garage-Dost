from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import math
import os

app = Flask(__name__)
CORS(app)

DATABASE = "garage_dost.db"


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Mechanics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mechanics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            online INTEGER DEFAULT 0
        )
    """)

    # Service Requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            vehicle_number TEXT NOT NULL,
            problem TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            mechanic_id INTEGER,
            status TEXT DEFAULT 'Searching'
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HOME / HTML PAGES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/customer-login")
def customer_login_page():
    return render_template("customer-login.html")


@app.route("/customer-register")
def customer_register_page():
    return render_template("customer-register.html")


@app.route("/request")
def request_page():
    return render_template("request.html")


@app.route("/mechanic-login")
def mechanic_login_page():
    return render_template("mechanic-login.html")


@app.route("/mechanic")
def mechanic_page():
    return render_template("mechanic.html")


@app.route("/tracking")
def tracking_page():
    return render_template("tracking.html")


@app.route("/payment")
def payment_page():
    return render_template("payment.html")


@app.route("/rating")
def rating_page():
    return render_template("rating.html")


# =========================
# CUSTOMER REGISTER
# =========================

@app.route("/customer/register", methods=["POST"])
def customer_register():

    data = request.json

    name = data.get("name")
    phone = data.get("phone")
    password = data.get("password")

    if not name or not phone or not password:
        return jsonify({
            "error": "All fields are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO customers
            (name, phone, password)
            VALUES (?, ?, ?)
        """, (
            name,
            phone,
            password
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            "error": "Phone number already registered"
        }), 409

    conn.close()

    return jsonify({
        "message": "Customer registered successfully"
    })


# =========================
# CUSTOMER LOGIN
# =========================

@app.route("/customer/login", methods=["POST"])
def customer_login():

    data = request.json

    phone = data.get("phone")
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM customers
        WHERE phone = ?
        AND password = ?
    """, (
        phone,
        password
    ))

    customer = cursor.fetchone()

    conn.close()

    if not customer:

        return jsonify({
            "error": "Invalid phone or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "customer": dict(customer)
    })


# =========================
# MECHANIC REGISTER
# =========================

@app.route("/mechanic/register", methods=["POST"])
def mechanic_register():

    data = request.json

    name = data.get("name")
    phone = data.get("phone")
    password = data.get("password")

    if not name or not phone or not password:

        return jsonify({
            "error": "All fields are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO mechanics
            (name, phone, password)
            VALUES (?, ?, ?)
        """, (
            name,
            phone,
            password
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            "error": "Mechanic phone already registered"
        }), 409

    conn.close()

    return jsonify({
        "message": "Mechanic registered successfully"
    })


# =========================
# MECHANIC LOGIN
# =========================

@app.route("/mechanic/login", methods=["POST"])
def mechanic_login():

    data = request.json

    phone = data.get("phone")
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM mechanics
        WHERE phone = ?
        AND password = ?
    """, (
        phone,
        password
    ))

    mechanic = cursor.fetchone()

    conn.close()

    if not mechanic:

        return jsonify({
            "error": "Invalid phone or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "mechanic": dict(mechanic)
    })


# =========================
# MECHANIC ONLINE
# =========================

@app.route("/mechanic/online", methods=["POST"])
def mechanic_online():

    data = request.json

    mechanic_id = data.get("mechanic_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    online = data.get("online", True)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE mechanics

        SET latitude = ?,
            longitude = ?,
            online = ?

        WHERE id = ?
    """, (
        latitude,
        longitude,
        1 if online else 0,
        mechanic_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Mechanic status updated"
    })


# =========================
# MECHANIC LIVE LOCATION
# =========================

@app.route("/mechanic/location", methods=["POST"])
def mechanic_location():

    data = request.json

    mechanic_id = data.get("mechanic_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not mechanic_id:
        return jsonify({
            "error": "Mechanic ID required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE mechanics

        SET latitude = ?,
            longitude = ?

        WHERE id = ?
    """, (
        latitude,
        longitude,
        mechanic_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Location updated"
    })


# =========================
# CREATE SERVICE REQUEST
# =========================

@app.route("/service/request", methods=["POST"])
def create_service_request():

    data = request.json

    customer_name = data.get("customer_name")
    customer_phone = data.get("customer_phone")
    vehicle_type = data.get("vehicle_type")
    vehicle_number = data.get("vehicle_number")
    problem = data.get("problem")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not all([
        customer_name,
        customer_phone,
        vehicle_type,
        vehicle_number,
        problem,
        latitude,
        longitude
    ]):

        return jsonify({
            "error": "All fields are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO service_requests
        (
            customer_name,
            customer_phone,
            vehicle_type,
            vehicle_number,
            problem,
            latitude,
            longitude
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_name,
        customer_phone,
        vehicle_type,
        vehicle_number,
        problem,
        latitude,
        longitude
    ))

    request_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Service request created",
        "request_id": request_id
    })


# =========================
# GET SERVICE REQUESTS
# =========================

@app.route("/service/requests", methods=["GET"])
def get_service_requests():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sr.*,

            m.latitude AS mechanic_latitude,
            m.longitude AS mechanic_longitude

        FROM service_requests sr

        LEFT JOIN mechanics m
        ON sr.mechanic_id = m.id

        WHERE sr.status != 'Completed'

        ORDER BY sr.id DESC
    """)

    requests = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(requests)


# =========================
# ACCEPT REQUEST
# =========================

@app.route("/service/accept", methods=["POST"])
def accept_request():

    data = request.json

    request_id = data.get("request_id")
    mechanic_id = data.get("mechanic_id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE service_requests

        SET mechanic_id = ?,
            status = 'Mechanic Accepted'

        WHERE id = ?
        AND status = 'Searching'
    """, (
        mechanic_id,
        request_id
    ))

    conn.commit()

    if cursor.rowcount == 0:

        conn.close()

        return jsonify({
            "error": "Request already accepted"
        }), 409

    conn.close()

    return jsonify({
        "message": "Request accepted"
    })


# =========================
# UPDATE SERVICE STATUS
# =========================

@app.route("/service/status", methods=["POST"])
def update_service_status():

    data = request.json

    request_id = data.get("request_id")
    status = data.get("status")

    allowed_statuses = [
        "Mechanic Accepted",
        "On the Way",
        "Arrived",
        "Repairing",
        "Completed"
    ]

    if status not in allowed_statuses:

        return jsonify({
            "error": "Invalid status"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE service_requests

        SET status = ?

        WHERE id = ?
    """, (
        status,
        request_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Status updated",
        "status": status
    })


# =========================
# DISTANCE CALCULATION
# =========================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))

    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# =========================
# FIND NEAREST MECHANIC
# =========================

@app.route(
    "/service/nearest-mechanic",
    methods=["POST"]
)
def nearest_mechanic():

    data = request.json

    customer_lat = data.get("latitude")
    customer_lon = data.get("longitude")

    if customer_lat is None or customer_lon is None:

        return jsonify({
            "error": "Customer location required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM mechanics
        WHERE online = 1
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
    """)

    mechanics = cursor.fetchall()

    conn.close()

    nearest = None
    shortest_distance = float("inf")

    for mechanic in mechanics:

        distance = calculate_distance(
            customer_lat,
            customer_lon,
            mechanic["latitude"],
            mechanic["longitude"]
        )

        if distance < shortest_distance:

            shortest_distance = distance
            nearest = dict(mechanic)

    if nearest is None:

        return jsonify({
            "message": "No online mechanic available"
        }), 404

    return jsonify({

        "mechanic": nearest,

        "distance_km":
            round(shortest_distance, 2)

    })


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    init_db()

    print("🚗 Garage Dost Backend Started!")
    print("🌐 http://localhost:5000")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
