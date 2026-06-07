from flask import Flask, jsonify
from dataclasses import dataclass, asdict

app = Flask(__name__)


@dataclass
class Product:
    id: int
    name: str
    price: float


_PRODUCTS = [
    Product(1, "Wireless Headphones", 79.99),
    Product(2, "USB-C Hub", 34.99),
    Product(3, "Mechanical Keyboard", 129.99),
]


@app.route("/api/products", methods=["GET"])
def get_products():
    """Return the full product catalogue as a JSON array."""
    return jsonify([asdict(p) for p in _PRODUCTS])


if __name__ == "__main__":
    app.run(debug=True)
