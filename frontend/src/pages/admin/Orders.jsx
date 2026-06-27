import { useEffect, useState } from "react";
import api, { apiError } from "../../api";
import {
  formatBRL,
  nextStatusFor,
  ORDER_TYPE_LABELS,
  PAYMENT_LABELS,
  STATUS_LABELS,
} from "../../lib";
import Modal from "../../components/Modal.jsx";

const STATUS_CLASS = {
  pending: "orange",
  confirmed: "orange",
  preparing: "orange",
  ready: "green",
  delivering: "green",
  completed: "gray",
  cancelled: "red",
};

export default function Orders() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);
  const [filter, setFilter] = useState("active");

  async function load() {
    try {
      const { data } = await api.get("/orders");
      setOrders(data);
    } catch (err) {
      setError(apiError(err));
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 15000); // refresh for new orders
    return () => clearInterval(t);
  }, []);

  async function setStatus(order, status) {
    const { data } = await api.patch(`/orders/${order.id}/status`, { status });
    setOrders((list) => list.map((o) => (o.id === data.id ? data : o)));
    if (detail?.id === order.id) setDetail(data);
  }

  if (!orders) return <div className="spinner" />;

  const filtered = orders.filter((o) => {
    if (filter === "active") return !["completed", "cancelled"].includes(o.status);
    if (filter === "done") return ["completed", "cancelled"].includes(o.status);
    return true;
  });

  return (
    <div className="stack">
      <div className="between">
        <h2>Pedidos</h2>
        <div className="center gap8">
          {[
            ["active", "Em aberto"],
            ["done", "Finalizados"],
            ["all", "Todos"],
          ].map(([k, label]) => (
            <button key={k} className={`pill ${filter === k ? "active" : ""}`} onClick={() => setFilter(k)}>
              {label}
            </button>
          ))}
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}

      {filtered.length === 0 && (
        <div className="card pad empty">Nenhum pedido por aqui ainda. 🍽️</div>
      )}

      <div className="orders-grid">
        {filtered.map((o) => {
          const next = nextStatusFor(o.order_type, o.status);
          return (
            <div key={o.id} className="card pad order-card">
              <div className="between">
                <strong>#{o.id} · {o.customer_name}</strong>
                <span className={`badge ${STATUS_CLASS[o.status]}`}>{STATUS_LABELS[o.status]}</span>
              </div>
              <div className="muted text-sm">
                {ORDER_TYPE_LABELS[o.order_type]} · {PAYMENT_LABELS[o.payment_method]} ·{" "}
                {new Date(o.created_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}
              </div>
              <div className="order-items-mini mt8">
                {o.items.map((it) => (
                  <div key={it.id} className="text-sm">
                    {it.quantity}× {it.name}
                    {it.options_summary && <span className="muted"> — {it.options_summary}</span>}
                  </div>
                ))}
              </div>
              <div className="between mt8">
                <span className="price">{formatBRL(o.total)}</span>
                <button className="btn ghost sm" onClick={() => setDetail(o)}>Detalhes</button>
              </div>
              <div className="center gap8 mt8">
                {next && (
                  <button className="btn sm grow" onClick={() => setStatus(o, next)}>
                    Avançar → {STATUS_LABELS[next]}
                  </button>
                )}
                {o.status !== "cancelled" && o.status !== "completed" && (
                  <button className="btn danger sm" onClick={() => setStatus(o, "cancelled")}>Cancelar</button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {detail && (
        <Modal title={`Pedido #${detail.id}`} onClose={() => setDetail(null)}>
          <div className="stack" style={{ gap: 10 }}>
            <div className="between">
              <span className={`badge ${STATUS_CLASS[detail.status]}`}>{STATUS_LABELS[detail.status]}</span>
              <span className="muted text-sm">
                {new Date(detail.created_at).toLocaleString("pt-BR")}
              </span>
            </div>
            <div>
              <strong>{detail.customer_name}</strong><br />
              <span className="muted">{detail.customer_phone}</span>
            </div>
            <div className="card pad" style={{ background: "var(--cream)" }}>
              <strong>{ORDER_TYPE_LABELS[detail.order_type]}</strong>
              {detail.order_type === "delivery" && (
                <div className="text-sm muted">
                  {detail.address_street}, {detail.address_number}
                  {detail.address_complement && ` - ${detail.address_complement}`}<br />
                  {detail.address_neighborhood}
                  {detail.address_reference && <><br />Ref.: {detail.address_reference}</>}
                </div>
              )}
              {detail.order_type === "dine_in" && detail.table_number && (
                <div className="text-sm muted">Mesa {detail.table_number}</div>
              )}
            </div>

            <div>
              {detail.items.map((it) => (
                <div key={it.id} className="between order-detail-item">
                  <div>
                    <strong>{it.quantity}× {it.name}</strong>
                    {it.options_summary && <div className="muted text-sm">{it.options_summary}</div>}
                  </div>
                  <span className="price">{formatBRL(it.total_price)}</span>
                </div>
              ))}
            </div>

            <hr className="divider" />
            <div className="between"><span className="muted">Subtotal</span><span>{formatBRL(detail.subtotal)}</span></div>
            {detail.delivery_fee > 0 && (
              <div className="between"><span className="muted">Entrega</span><span>{formatBRL(detail.delivery_fee)}</span></div>
            )}
            <div className="between"><strong>Total</strong><strong className="price">{formatBRL(detail.total)}</strong></div>

            <div className="card pad" style={{ background: "var(--cream)" }}>
              <strong>Pagamento: {PAYMENT_LABELS[detail.payment_method]}</strong>
              {detail.payment_method === "cash" && detail.change_for > 0 && (
                <div className="text-sm muted">Troco para {formatBRL(detail.change_for)}</div>
              )}
              {detail.payment_method === "pix" && detail.pix_payload && (
                <div className="text-sm muted">PIX gerado para o cliente.</div>
              )}
            </div>
            {detail.notes && (
              <div><strong>Observações:</strong> <span className="muted">{detail.notes}</span></div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
