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
