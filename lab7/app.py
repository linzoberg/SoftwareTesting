from flask import Flask, request, jsonify
from converter import CurrencyConverter

app = Flask(__name__)
converter = CurrencyConverter()


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
            "from": from_cur.upper(),
            "to": to_cur.upper(),
            "rate": rate
        })
    except TypeError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/convert", methods=["GET"])
def convert():
    """GET /api/convert?from=USD&to=EUR&amount=100 — конвертировать сумму."""
    from_cur = request.args.get("from")
    to_cur = request.args.get("to")
    amount_str = request.args.get("amount")

    if not from_cur or not to_cur or amount_str is None:
        return jsonify({"error": "Параметры 'from', 'to' и 'amount' обязательны"}), 400

    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Параметр 'amount' должен быть числом"}), 400

    try:
        result = converter.convert(amount, from_cur, to_cur)
        rate = converter.get_rate(from_cur, to_cur)
        return jsonify({
            "success": True,
            "from": from_cur.upper(),
            "to": to_cur.upper(),
            "amount": amount,
            "rate": rate,
            "result": result
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


@app.route("/api/health", methods=["GET"])
def health():
    """GET /api/health — проверка работоспособности сервера."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("Запуск сервера конвертера валют...")
    print("Доступные эндпоинты:")
    print("  GET http://127.0.0.1:5000/api/health")
    print("  GET http://127.0.0.1:5000/api/rate?from=USD&to=EUR")
    print("  GET http://127.0.0.1:5000/api/convert?from=USD&to=EUR&amount=100")
    print("  GET http://127.0.0.1:5000/api/currencies")
    app.run(debug=True)