from typing import List, Optional
from models import Order, OrderItem, Product
from repository import IOrderRepository


class OrderService:
    def __init__(self, repository: IOrderRepository) -> None:
        self._repository = repository

    def create_order(self, customer_id: str) -> Order:
        order = Order(customer_id=customer_id)
        self._repository.save(order)
        return order

    def add_item(self, order_id: str, product: Product, quantity: int) -> Order:
        order = self._repository.find_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        if not product.is_available(quantity):
            raise ValueError(f"Insufficient stock for {product.name}")
        order.add_item(OrderItem(product=product, quantity=quantity))
        self._repository.save(order)
        return order

    def confirm_order(self, order_id: str) -> Order:
        order = self._repository.find_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        order.confirm()
        self._repository.save(order)
        return order

    def get_customer_orders(self, customer_id: str) -> List[Order]:
        return self._repository.find_by_customer(customer_id)
