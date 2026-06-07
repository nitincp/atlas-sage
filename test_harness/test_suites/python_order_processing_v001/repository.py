from abc import ABC, abstractmethod
from typing import List, Optional
from models import Order


class IOrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> str:
        ...

    @abstractmethod
    def find_by_id(self, order_id: str) -> Optional[Order]:
        ...

    @abstractmethod
    def find_by_customer(self, customer_id: str) -> List[Order]:
        ...


class OrderRepository(IOrderRepository):
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def save(self, order: Order) -> str:
        self._store[order.order_id] = order
        return order.order_id

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._store.get(order_id)

    def find_by_customer(self, customer_id: str) -> List[Order]:
        return [o for o in self._store.values() if o.customer_id == customer_id]
