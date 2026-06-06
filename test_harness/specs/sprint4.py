"""Sprint 4 — Correction Capture (Loop 1 / Domain SSR).

Language: Python (same mini-app as sprint1/sprint3)
Thesis claim: Human corrections to speculative answers are captured as permanent graph
              knowledge and surface in subsequent queries.

What this sprint validates:
  AS-29  Correction capture — SME flags wrong answer inline (capture_correction tool wired)
  AS-30  Correction stored against node in the graph (write_correction + get_corrections)
  AS-31  Correction history injected into re-summarisation prompts on next ingestion run
  AS-32  Correction history visible to Tier-2 in subsequent queries (get_corrections in query loop)
  AS-33  Verified: post-correction query references the SME's correction (keyword assertion)

Test flow:
  1. Ingest the 4-file order-processing mini-app (same files as sprint1/sprint3)
  2. Q1 (baseline): query about how OrderService uses IOrderRepository — system speculates
  3. Harness injects a programmatic correction against the OrderService node:
       original  → system claimed direct per-operation repository calls
       corrected → SME says Unit of Work pattern: operations grouped atomically
  4. Q2 (post-correction): same question — system must surface the correction
  5. Assert: Q2 answer contains a keyword from the correction text ("unit of work" / "atomic")
"""

from atlas_sage.testing.runner import CorrectionSpec, QuerySpec, SprintSpec

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

SPEC = SprintSpec(
    name="sprint4",
    suite_name="python_order_processing",
    findings=[
        "search_corrections called before vector_search confirmed — correction surfaced as first line of Q2 answer ('SME Correction on Record: Unit of Work pattern...')",
        "get_corrections(node_id) per-node loop is unreliable — LLM checks a subset of returned nodes; node_id match depends on LLM selection order. Replaced with search_corrections(query_text) called once upfront.",
        "Correction stored with logical concept name as target_id ('orderservice') not UUID — text search over target_id+original+corrected is node_id-independent and stable across ingestion runs.",
        "Q1 baseline correctly reported no prior corrections — the 'no corrections = structural inference only' path works as designed.",
        "Domain SSR loop closes: speculative Q1 answer provoked correction; Q2 answer led with SME knowledge, then grounded it in graph structure.",
        "Cost: ~$0.52/run vs sprint3 $0.41 — extra search_corrections call per query is the delta (~$0.05 per query pair).",
    ],
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
            name="q1_baseline",
            question=(
                "How does OrderService interact with IOrderRepository? "
                "Describe the relationship and the pattern used."
            ),
            # Baseline: system speculates from structure alone — no correction yet
            expected_keywords=["orderservice", "iorderrepository", "repository", "service"],
            min_length=100,
        ),
        QuerySpec(
            name="q2_post_correction",
            question=(
                "How does OrderService interact with IOrderRepository? "
                "Describe the relationship and the pattern used."
            ),
            # Post-correction: system must surface the SME-injected Unit of Work knowledge.
            # Keywords are intentionally domain-specific — they only appear if the correction
            # was retrieved and referenced; "correction" / "corrected" are excluded because
            # "No corrections found" would accidentally satisfy them.
            expected_keywords=["unit of work", "atomic", "atomically"],
            min_length=100,
        ),
    ],
    correction=CorrectionSpec(
        after_query="q1_baseline",
        target_node_keyword="orderservice",
        original=(
            "OrderService calls the repository directly for each operation in isolation, "
            "with no explicit transaction grouping."
        ),
        corrected=(
            "OrderService applies the Unit of Work pattern: all repository operations within "
            "a business flow (create, add item, confirm) are logically grouped and committed "
            "atomically to maintain consistency across the order lifecycle."
        ),
        session_id="sprint4_harness",
    ),
)
