"""Sprint 2 — TypeScript ingestion via ts-morph, no code change required.

Language: TypeScript (ts-morph — TypeScript Compiler API; Node.js runtime)
Thesis claim: Skill system self-extends without code change (Sprint 2)
"""
from atlas_sage.testing.runner import QuerySpec, SprintSpec

SAMPLE_MODELS = """\
export interface Product {
  productId: string;
  name: string;
  price: number;
  stock: number;
}

export interface OrderItem {
  product: Product;
  quantity: number;
  readonly subtotal: number;
}

export interface Order {
  orderId: string;
  customerId: string;
  items: OrderItem[];
  status: string;
  readonly total: number;
}

export class ProductImpl implements Product {
  constructor(
    public productId: string = crypto.randomUUID(),
    public name: string = '',
    public price: number = 0,
    public stock: number = 0,
  ) {}

  isAvailable(quantity: number): boolean {
    return this.stock >= quantity;
  }
}

export class OrderItemImpl implements OrderItem {
  constructor(
    public product: Product,
    public quantity: number,
  ) {}

  get subtotal(): number {
    return this.product.price * this.quantity;
  }
}

export class OrderImpl implements Order {
  public orderId: string;
  public customerId: string;
  public items: OrderItem[];
  public status: string;

  constructor(customerId: string) {
    this.orderId = crypto.randomUUID();
    this.customerId = customerId;
    this.items = [];
    this.status = 'pending';
  }

  get total(): number {
    return this.items.reduce((sum, item) => sum + item.subtotal, 0);
  }

  addItem(item: OrderItem): void {
    this.items.push(item);
  }

  confirm(): void {
    if (this.items.length === 0) {
      throw new Error('Cannot confirm empty order');
    }
    this.status = 'confirmed';
  }
}
"""

SAMPLE_REPOSITORY = """\
import { Order } from './models';

export interface IOrderRepository {
  save(order: Order): string;
  findById(orderId: string): Order | undefined;
  findByCustomer(customerId: string): Order[];
}

export class OrderRepository implements IOrderRepository {
  private store: Map<string, Order> = new Map();

  save(order: Order): string {
    this.store.set(order.orderId, order);
    return order.orderId;
  }

  findById(orderId: string): Order | undefined {
    return this.store.get(orderId);
  }

  findByCustomer(customerId: string): Order[] {
    return Array.from(this.store.values()).filter(
      (o) => o.customerId === customerId,
    );
  }
}
"""

SAMPLE_SERVICE = """\
import { Order, OrderImpl, OrderItemImpl, Product } from './models';
import { IOrderRepository } from './repository';

export class OrderService {
  constructor(private readonly repository: IOrderRepository) {}

  createOrder(customerId: string): Order {
    const order = new OrderImpl(customerId);
    this.repository.save(order);
    return order;
  }

  addItem(orderId: string, product: Product, quantity: number): Order {
    const order = this.repository.findById(orderId);
    if (!order) throw new Error(`Order ${orderId} not found`);
    const item = new OrderItemImpl(product, quantity);
    (order as OrderImpl).addItem(item);
    this.repository.save(order);
    return order;
  }

  confirmOrder(orderId: string): Order {
    const order = this.repository.findById(orderId);
    if (!order) throw new Error(`Order ${orderId} not found`);
    (order as OrderImpl).confirm();
    this.repository.save(order);
    return order;
  }

  getCustomerOrders(customerId: string): Order[] {
    return this.repository.findByCustomer(customerId);
  }
}
"""

SAMPLE_CONTROLLER = """\
import { Product } from './models';
import { OrderService } from './service';

export class OrderController {
  constructor(private readonly service: OrderService) {}

  handleCreateOrder(customerId: string): Record<string, unknown> {
    const order = this.service.createOrder(customerId);
    return { orderId: order.orderId, status: order.status };
  }

  handleAddItem(
    orderId: string,
    productData: Record<string, unknown>,
    quantity: number,
  ): Record<string, unknown> {
    const product: Product = {
      productId: crypto.randomUUID(),
      name: productData['name'] as string,
      price: productData['price'] as number,
      stock: (productData['stock'] as number) ?? 0,
    };
    const order = this.service.addItem(orderId, product, quantity);
    return { orderId: order.orderId, total: order.total, itemCount: order.items.length };
  }

  handleConfirmOrder(orderId: string): Record<string, unknown> {
    const order = this.service.confirmOrder(orderId);
    return { orderId: order.orderId, status: order.status, total: order.total };
  }

  handleGetCustomerOrders(customerId: string): Record<string, unknown>[] {
    return this.service.getCustomerOrders(customerId).map((o) => ({
      orderId: o.orderId,
      status: o.status,
      total: o.total,
    }));
  }
}
"""

SPEC = SprintSpec(
    name="sprint2",
    suite_name="typescript_order_processing",
    files={
        "models.ts": SAMPLE_MODELS,
        "repository.ts": SAMPLE_REPOSITORY,
        "service.ts": SAMPLE_SERVICE,
        "controller.ts": SAMPLE_CONTROLLER,
    },
    pattern="**/*.ts",
    min_nodes=8,
    min_source_files=3,
    expected_edge_types={"IMPLEMENTS", "INJECTS", "IMPORTS", "CALLS"},
    native_parser_keyword="ts-morph",
    required_execution_environment="node",
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
