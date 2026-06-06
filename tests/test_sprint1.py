"""Sprint 1 validation — multi-file Python ingestion, graph edges, traversal, blast radius.

Language: Python (built-in ast — no extra tooling, rich OOP: INHERITS, INJECTS, CALLS, IMPLEMENTS)
Thesis claim: Structured Speculation anchored to graph produces useful output (Sprint 1)

Edge types exercised:
  IMPLEMENTS — deterministic (class OrderRepository(IOrderRepository))
  INJECTS    — deterministic (constructor parameter typed as interface)
  CALLS      — probabilistic (method invocations)
  RETURNS    — deterministic (return type annotations)

AS-10  Multi-file ingestion via ingest_directory
AS-11  Edge extraction: IMPLEMENTS, INJECTS, CALLS, RETURNS
AS-12  Edge confidence metadata stored and validated
AS-13  graph_traverse wired at query time (exercised via blast-radius query)
AS-14  Orchestrator classifies query intent → correct direction + depth
AS-15  Blast radius: inbound traversal identifies all impacted classes

Run:
    pytest tests/test_sprint1.py -v -s

Artifacts saved to: test_runs/sprint1/<timestamp>/
"""

from __future__ import annotations

import shutil

import pytest

from atlas_sage.testing.runner import QuerySpec, SprintSpec, run_sprint

# ---------------------------------------------------------------------------
# Sample Python mini-app — 4 files, layered architecture, all edge types
# ---------------------------------------------------------------------------

SAMPLE_MODELS = """\
from dataclasses import dataclass, field
from typing import List
import uuid


@dataclass
class Product:
    product_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    price: float = 0.0
    stock: int = 0

    def is_available(self, quantity: int) -> bool:
        return self.stock >= quantity


@dataclass
class OrderItem:
    product: Product
    quantity: int

    @property
    def subtotal(self) -> float:
        return self.product.price * self.quantity


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    items: List[OrderItem] = field(default_factory=list)
    status: str = "pending"

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    def confirm(self) -> None:
        if not self.items:
            raise ValueError("Cannot confirm empty order")
        self.status = "confirmed"
"""

SAMPLE_REPOSITORY = """\
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
"""

SAMPLE_SERVICE = """\
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
"""

SAMPLE_CONTROLLER = """\
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
"""

# ---------------------------------------------------------------------------
# Sprint 1 specification — data only, no test logic
# ---------------------------------------------------------------------------

SPRINT1 = SprintSpec(
    name="sprint1",
    suite_name="python_order_processing",
    files={
        "models.py": SAMPLE_MODELS,
        "repository.py": SAMPLE_REPOSITORY,
        "service.py": SAMPLE_SERVICE,
        "controller.py": SAMPLE_CONTROLLER,
    },
    pattern="**/*.py",
    min_nodes=8,
    min_source_files=3,
    expected_edge_types={"IMPLEMENTS", "INJECTS", "CALLS", "INHERITS", "RETURNS"},
    native_parser_keyword="ast",
    queries=[
        QuerySpec(
            name="blast_radius",
            question=(
                "What is the blast radius if IOrderRepository changes? "
                "Which classes and files would be impacted?"
            ),
            expected_keywords=["orderrepository", "orderservice", "service", "repository"],
        ),
        QuerySpec(
            name="dependency",
            question="What does OrderService depend on? What are its dependencies?",
            expected_keywords=["repository", "iorderrepository", "order", "model"],
        ),
    ],
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def config():
    try:
        from atlas_sage.config import Config
        return Config()
    except EnvironmentError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="module")
def temp_db(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("sprint1_db"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(scope="module")
def src_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("sprint1_src")
    for name, content in SPRINT1.files.items():
        (d / name).write_text(content)
    return str(d)


# ---------------------------------------------------------------------------
# Test — one function, all assertions delegated to assert_sprint()
# ---------------------------------------------------------------------------


def test_sprint1(config, temp_db, src_dir):
    """AS-10 through AS-15: ingest, edges, native parser, graph traversal, blast radius."""
    artifact = run_sprint(SPRINT1, config, temp_db, src_dir)
    # assertions ran inside run_sprint; raises AssertionError on failure
    print(f"\nNodes: {len(artifact.nodes)} | Edges: {len(artifact.edges)} | {artifact.duration_s:.0f}s")
    print(f"Skill: {artifact.skill.get('name')} ({artifact.skill.get('tool_name')})")
    print(f"Artifacts: {artifact.run_dir}")
