from flask import Flask, request, jsonify, render_template
@app.route("/service/nearest-mechanic", methods=["POST"])
def nearest_mechanic():

    data = request.json

    customer_lat = data.get("latitude")
    customer_lon = data.get("longitude")

    if customer_lat is None or customer_lon is None:
        return jsonify({
            "error": "Customer location required"
        }), 400

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM mechanics
        WHERE online = 1
    """)

    mechanics = cursor.fetchall()

    nearest = None
    shortest_distance = float("inf")

    for mechanic in mechanics:

        if mechanic["latitude"] is None:
            continue

        if mechanic["longitude"] is None:
            continue

        distance = calculate_distance(
            customer_lat,
            customer_lon,
            mechanic["latitude"],
            mechanic["longitude"]
        )

        if distance < shortest_distance:

            shortest_distance = distance
            nearest = dict(mechanic)

    conn.close()

    if nearest is None:
        return jsonify({
            "message": "No online mechanic available"
        }), 404

    return jsonify({
        "mechanic": nearest,
        "distance_km": round(shortest_distance, 2)
    })
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/customer-login")
def customer_login():
    return render_template("customer-login.html")


@app.route("/customer-register")
def customer_register():
    return render_template("customer-register.html")


@app.route("/request")
def service_request():
    return render_template("request.html")


@app.route("/mechanic-login")
def mechanic_login():
    return render_template("mechanic-login.html")


@app.route("/mechanic")
def mechanic_page():
    return render_template("mechanic.html")


@app.route("/tracking")
def tracking():
    return render_template("tracking.html")


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/rating")
def rating():
    return render_template("rating.html")
