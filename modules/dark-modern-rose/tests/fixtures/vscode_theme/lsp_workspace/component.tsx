// Fixture for tests/vscode_theme/e2e.mjs: colours that need tsserver semantic tokens.
import { useState } from "react";

export const API_URL = "https://example.com";
enum Status { Open = "open", Closed = "closed" }

type Order = { id: number; status: Status };

class OrderStore {
  cache = new Map<number, Order>();
}

export function OrderList({ orders }: { orders: Order[] }) {
  const [query, setQuery] = useState("");
  let count = 0;
  const visible = orders.filter((o) => o.status === Status.Open);
  const options = { limit: 10, query };
  const store = new OrderStore();
  count += visible.length + options.limit + store.cache.size;
  return (
    <ul className="orders" data-count={count}>
      {visible.map((order) => (
        <Row key={order.id} order={order} onPick={() => setQuery(API_URL)} />
      ))}
    </ul>
  );
}

function Row(props: { order: Order; onPick: () => void }) {
  return <li onClick={props.onPick}>{props.order.id}</li>;
}
