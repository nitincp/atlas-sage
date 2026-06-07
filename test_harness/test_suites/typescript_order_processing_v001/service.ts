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
