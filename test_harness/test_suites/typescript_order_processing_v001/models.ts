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
