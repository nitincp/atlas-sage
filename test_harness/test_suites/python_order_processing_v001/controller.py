from typing import Any, Dict, List
from service import OrderService
from models import Product


class OrderController:
    def __init__(self, service: OrderService) -> None:
        self._service = service

    def handle_create_order(self, customer_id: str) -> Dict[str, Any]:
        order = self._service.create_order(customer_id)
        return {"order_id": order.order_id, "status": order.status}

    def handle_add_item(
        self, order_id: str, product_data: Dict[str, Any], quantity: int
    ) -> Dict[str, Any]:
        product = Product(
            name=product_data["name"],
            price=product_data["price"],
            stock=product_data.get("stock", 0),
        )
        order = self._service.add_item(order_id, product, quantity)
        return {"order_id": order.order_id, "total": order.total, "item_count": len(order.items)}

    def handle_confirm_order(self, order_id: str) -> Dict[str, Any]:
        order = self._service.confirm_order(order_id)
        return {"order_id": order.order_id, "status": order.status, "total": order.total}

    def handle_get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        orders = self._service.get_customer_orders(customer_id)
        return [{"order_id": o.order_id, "status": o.status, "total": o.total} for o in orders]
