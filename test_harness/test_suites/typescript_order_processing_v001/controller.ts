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
