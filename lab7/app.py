from flask import Flask, request, jsonify
from converter import CurrencyConverter

app = Flask(__name__)
converter = CurrencyConverter()

# Хранилище для избранных валютных пар (в памяти сервера)
favorite_pairs = []
next_id = 1

# Настройки конвертера (в памяти сервера)
settings = {
    "decimal_places": 2,
    "default_base": "USD",
    "timeout": 10
}


# =============================================
# GET — получение данных
# =============================================

@app.route("/api/health", methods=["GET"])
def health():
    """GET /api/health — проверка работоспособности сервера."""
    return jsonify({"status": "ok"})


@app.route("/api/rate", methods=["GET"])
def get_rate():
    """GET /api/rate?from=USD&to=EUR — получить курс обмена."""
    from_cur = request.args.get("from")
    to_cur = request.args.get("to")

    if not from_cur or not to_cur:
        return jsonify({"error": "Параметры 'from' и 'to' обязательны"}), 400

    try:
        rate = converter.get_rate(from_cur, to_cur)
        return jsonify({
            "success": True,
            "from": from_cur.strip().upper(),
            "to": to_cur.strip().upper(),
            "rate": rate
        })
    except TypeError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/currencies", methods=["GET"])
def get_currencies():
    """GET /api/currencies — список доступных валют."""
    try:
        currencies = converter.get_available_currencies()
        return jsonify({
            "success": True,
            "count": len(currencies),
            "currencies": currencies
        })
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/favorites", methods=["GET"])
def get_favorites():
    """GET /api/favorites — получить список избранных валютных пар."""
    return jsonify({
        "success": True,
        "count": len(favorite_pairs),
        "favorites": favorite_pairs
    })


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """GET /api/settings — получить текущие настройки."""
    return jsonify({
        "success": True,
        "settings": settings
    })


# =============================================
# POST — создание ресурсов / выполнение операций
# =============================================

@app.route("/api/convert", methods=["POST"])
def convert():
    """POST /api/convert — конвертировать сумму (JSON body)."""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Тело запроса должно быть в формате JSON"}), 400

    from_cur = data.get("from")
    to_cur = data.get("to")
    amount = data.get("amount")

    if not from_cur or not to_cur or amount is None:
        return jsonify({"error": "Поля 'from', 'to' и 'amount' обязательны"}), 400

    if not isinstance(amount, (int, float)):
        return jsonify({"error": "Поле 'amount' должно быть числом"}), 400

    try:
        result = converter.convert(amount, from_cur, to_cur)
        rate = converter.get_rate(from_cur, to_cur)
        return jsonify({
            "success": True,
            "from": from_cur.strip().upper(),
            "to": to_cur.strip().upper(),
            "amount": amount,
            "rate": rate,
            "result": result
        }), 200
    except TypeError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    """POST /api/favorites — добавить валютную пару в избранное."""
    global next_id

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Тело запроса должно быть в формате JSON"}), 400

    from_cur = data.get("from")
    to_cur = data.get("to")

    if not from_cur or not to_cur:
        return jsonify({"error": "Поля 'from' и 'to' обязательны"}), 400

    from_cur = from_cur.strip().upper()
    to_cur = to_cur.strip().upper()

    # Проверка на дубликат
    for pair in favorite_pairs:
        if pair["from"] == from_cur and pair["to"] == to_cur:
            return jsonify({"error": "Такая пара уже в избранном"}), 409

    new_pair = {
        "id": next_id,
        "from": from_cur,
        "to": to_cur
    }
    favorite_pairs.append(new_pair)
    next_id += 1

    return jsonify({
        "success": True,
        "message": "Пара добавлена в избранное",
        "favorite": new_pair
    }), 201


# =============================================
# PUT — полное обновление ресурса
# =============================================

@app.route("/api/settings", methods=["PUT"])
def update_settings():
    """PUT /api/settings — полное обновление настроек."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Тело запроса должно быть в формате JSON"}), 400

    # PUT требует ВСЕ поля
    if "decimal_places" not in data or "default_base" not in data or "timeout" not in data:
        return jsonify({
            "error": "PUT требует все поля: 'decimal_places', 'default_base', 'timeout'"
        }), 400

    if not isinstance(data["decimal_places"], int) or data["decimal_places"] < 0:
        return jsonify({"error": "'decimal_places' должно быть неотрицательным целым числом"}), 422

    if not isinstance(data["timeout"], (int, float)) or data["timeout"] <= 0:
        return jsonify({"error": "'timeout' должен быть положительным числом"}), 422

    settings["decimal_places"] = data["decimal_places"]
    settings["default_base"] = data["default_base"].strip().upper()
    settings["timeout"] = data["timeout"]

    return jsonify({
        "success": True,
        "message": "Настройки обновлены",
        "settings": settings
    })


# =============================================
# PATCH — частичное обновление ресурса
# =============================================

@app.route("/api/settings", methods=["PATCH"])
def patch_settings():
    """PATCH /api/settings — частичное обновление настроек."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Тело запроса должно быть в формате JSON"}), 400

    if "decimal_places" in data:
        if not isinstance(data["decimal_places"], int) or data["decimal_places"] < 0:
            return jsonify({"error": "'decimal_places' должно быть неотрицательным целым числом"}), 422
        settings["decimal_places"] = data["decimal_places"]

    if "default_base" in data:
        settings["default_base"] = data["default_base"].strip().upper()

    if "timeout" in data:
        if not isinstance(data["timeout"], (int, float)) or data["timeout"] <= 0:
            return jsonify({"error": "'timeout' должен быть положительным числом"}), 422
        settings["timeout"] = data["timeout"]

    return jsonify({
        "success": True,
        "message": "Настройки частично обновлены",
        "settings": settings
    })


# =============================================
# DELETE — удаление ресурса
# =============================================

@app.route("/api/favorites/<int:pair_id>", methods=["DELETE"])
def delete_favorite(pair_id):
    """DELETE /api/favorites/{id} — удалить валютную пару из избранного."""
    for i, pair in enumerate(favorite_pairs):
        if pair["id"] == pair_id:
            deleted = favorite_pairs.pop(i)
            return jsonify({
                "success": True,
                "message": "Пара удалена из избранного",
                "deleted": deleted
            })

    return jsonify({"error": f"Пара с id={pair_id} не найдена"}), 404


if __name__ == "__main__":
    print("=" * 50)
    print("Сервер конвертера валют")
    print("=" * 50)
    print("Эндпоинты:")
    print("  GET    /api/health")
    print("  GET    /api/rate?from=USD&to=EUR")
    print("  GET    /api/currencies")
    print("  GET    /api/favorites")
    print("  GET    /api/settings")
    print("  POST   /api/convert          (JSON body)")
    print("  POST   /api/favorites        (JSON body)")
    print("  PUT    /api/settings          (JSON body)")
    print("  PATCH  /api/settings          (JSON body)")
    print("  DELETE /api/favorites/{id}")
    print("=" * 50)
    app.run(debug=True)