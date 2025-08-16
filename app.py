from flask import Flask, jsonify, request, abort
import requests

app = Flask(__name__)
PORT = 5000

BASE_URL = "https://api.chucknorris.io/jokes"

def fetch_categories():
    """Obtiene categorías desde la API pública (sin cache)."""
    r = requests.get(f"{BASE_URL}/categories", timeout=10)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError("Respuesta inválida de categorías")
    return data

@app.route("/categories", methods=["GET"])
def get_categories():
    try:
        cats = fetch_categories()
        return jsonify(cats), 200
    except requests.RequestException as e:
        return jsonify({"error": "No se pudieron obtener categorías", "detalles": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500

@app.route("/joke/<string:category>", methods=["GET"])
def get_joke_by_category(category):
    if not category or not isinstance(category, str):
        return jsonify({"error": "Solicitud fallida", "message": "Category requerida"}), 400

    try:
        categories = fetch_categories()
        if category not in categories:
            return jsonify({
                "error": "Solicitud fallida",
                "message": f"Categoría inválida '{category}'. Usa /categories para ver opciones válidas."
            }), 400

        #chiste por categoría
        r = requests.get(f"{BASE_URL}/random", params={"category": category}, timeout=10)
        if not r.ok:
            return jsonify({"error": "Bad Gateway", "message": f"Upstream error: {r.status_code}"}), 502

        j = r.json()
        return jsonify({
            "id": j.get("id", "unknown"),
            "url": j.get("url", ""),
            "category": category,
            "value": j.get("value", "")
        }), 200

    except requests.RequestException as e:
        return jsonify({"error": "No se pudo obtener el chiste", "detalles": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500

# ----------------BONUS::----------------------
@app.route("/search", methods=["GET"])
def search_jokes():
    term = request.args.get("query", "").strip()
    if not term:
        return jsonify({"error": "Solicitud fallida", "message": "Parámetro 'query' es requerido"}), 400

    try:
        r = requests.get(f"{BASE_URL}/search", params={"query": term}, timeout=10)
        if not r.ok:
            return jsonify({"error": "Bad Gateway", "message": f"Upstream error: {r.status_code}"}), 502

        data = r.json()
        total = data.get("total", 0)
        results = data.get("result", [])

        if total == 0 or not results:
            return jsonify({"message": f"No se encontraron chistes para '{term}'"}), 404

        jokes = [
            {
                "id": it.get("id", "unknown"),
                "url": it.get("url", ""),
                "categories": it.get("categories", []),
                "value": it.get("value", "")
            } for it in results
        ]
        return jsonify({"total": total, "results": jokes}), 200

    except requests.RequestException as e:
        return jsonify({"error": "No se pudo realizar la búsqueda", "detalles": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500

@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not Found", "message": "Ruta no encontrada"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal Server Error", "detalles": str(e)}), 500

if __name__ == "__main__":
    app.run(port=PORT, debug=True)
