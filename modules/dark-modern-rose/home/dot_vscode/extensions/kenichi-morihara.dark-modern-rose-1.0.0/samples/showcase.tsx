// Dark Modern Rose: React + TypeScript showcase (check colours here).
import React, { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

/**
 * Order list with filters.
 * @param props - the component props
 * @returns {JSX.Element} the rendered list
 */
export const API_URL = "https://example.com/api";
const MAX_ITEMS = 50;
export const defaultFilter = { status: "open", limit: 10 };

enum Status {
  Open = "open",
  Closed = "closed",
}

interface OrderProps<T extends Order = Order> {
  orders: T[];
  title?: string;
  onSelect: (order: T) => void;
  children?: ReactNode;
}

type Order = { id: number; total: number; status: Status };

class OrderStore {
  private readonly cache = new Map<number, Order>();
  static instance: OrderStore | null = null;

  constructor(public name: string) {}

  async load(id: number): Promise<Order | undefined> {
    const hit = this.cache.get(id);
    if (hit) return hit;
    const res = await fetch(`${API_URL}/orders/${id}?limit=${MAX_ITEMS}`);
    return (await res.json()) as Order;
  }
}

export function OrderList({ orders, title = "Orders", onSelect, children }: OrderProps) {
  const [query, setQuery] = useState<string>("");
  let count = 0;
  const visible = useMemo(() => orders.filter((o) => o.status === Status.Open && o.total > 0), [orders]);

  useEffect(() => {
    count += visible.length;
    if (typeof window !== "undefined" && visible.length > MAX_ITEMS) {
      console.warn("too many", count);
    } else {
      setQuery(null ?? "");
    }
  }, [visible]);

  const handleClick = (order: Order) => () => onSelect(order);

  return (
    <section className="orders" data-count={visible.length}>
      <h1>{title}</h1>
      {visible.length === 0 ? <p>No orders</p> : null}
      <ul>
        {visible.map((order) => (
          <OrderRow key={order.id} order={order} onClick={handleClick(order)} disabled={false} />
        ))}
      </ul>
      {children}
    </section>
  );
}

const OrderRow = ({ order, onClick }: { order: Order; onClick: () => void; disabled?: boolean }) => (
  <li onClick={onClick}>#{order.id}: {order.total.toFixed(2)}</li>
);

export default OrderList;
