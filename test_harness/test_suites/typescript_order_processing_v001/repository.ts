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
