import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { shopApi } from "../../api";
import { useCustomerAuth } from "../../customerAuth.jsx";
import {
  formatBRL,
  ORDER_TYPE_LABELS,
  PAYMENT_LABELS,
  STATUS_LABELS,
  statusFlowFor,
} from "../../lib";
import { getGuestOrderIds } from "./orderStore.js";
import iconLogo from "../../assets/yumi_icon.png";
import PixView from "../../components/PixView.jsx";
import CustomerAuthModal from "./CustomerAuthModal.jsx";

const ACTIVE = (s) => !["completed", "cancelled"].includes(s);

function StatusTracker({ order }) {
  if (order.status === "cancelled") {
    return <div className="badge red" style={{ marginTop: 8 }}>Pedido cancelado</div>;
  }
  let flow = statusFlowFor(order.order_type);
  // be defensive: if the order somehow has a status outside this type's flow
  // (e.g. legacy data), insert it before "completed" so the tracker still works
  if (!flow.includes(order.status)) {
    flow = [...flow.slice(0, -1), order.status, "completed"];
  }
  const current = flow.indexOf(order.status);
  return (
    <div className="tracker">
      {flow.map((s, i) => (
        <div key={s} className={`tracker-step ${i <= current ? "done" : ""} ${i === current ? "current" : ""}`}>
          <span className="tracker-dot">{i < current ? "✓" : i + 1}</span>
          <span className="tracker-label">{STATUS_LABELS[s]}</span>
        </div>
      ))}
    </div>
  );
}

function OrderCard({ order, defaultOpen }) {
  const [showPix, setShowPix] = useState(false);
  return (
    <div className={`card pad order-track-card ${ACTIVE(order.status) ? "active" : ""}`}>
      <div className="between">
        <div>
          <strong>Pedido #{order.id}</strong>
          <div className="muted text-sm">
            {ORDER_TYPE_LABELS[order.order_type]} · {PAYMENT_LABELS[order.payment_method]} ·{" "}
            {new Date(order.created_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}
          </div>
        </div>
        <span className="price">{formatBRL(order.total)}</span>
      </div>

      <StatusTracker order={order} />

      <div className="order-track-items mt8">
        {order.items.map((it) => (
          <div key={it.id} className="text-sm">
            {it.quantity}× {it.name}
            {it.options_summary && <span className="muted"> — {it.options_summary}</span>}
          </div>
        ))}
      </div>

      {order.payment_method === "pix" && order.pix_payload && ACTIVE(order.status) && (
        <div className="mt8">
          <button className="btn ghost sm" onClick={() => setShowPix((v) => !v)}>
            {showPix ? "Esconder PIX" : "💠 Pagar com PIX"}
          </button>
          {showPix && (
            <div className="mt8"><PixView payload={order.pix_payload} amount={order.total} /></div>
          )}
        </div>
      )}
    </div>
  );
}

export default function CustomerOrders() {
  const { empresaUrl } = useParams();
  const navigate = useNavigate();
  const { customer, loading: authLoading, logout } = useCustomerAuth();
  const [company, setCompany] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [authModal, setAuthModal] = useState(false);

  const load = useCallback(async () => {
    const byId = new Map();
    // logged-in customer's orders at this store
    if (customer) {
      try {
        const { data } = await shopApi.get(`/customer/orders?empresa_url=${empresaUrl}`);
        data.forEach((o) => byId.set(o.id, o));
      } catch { /* ignore */ }
    }
    // guest orders placed from this device
    const guestIds = getGuestOrderIds(empresaUrl).filter((id) => !byId.has(id));
    await Promise.all(
      guestIds.map(async (id) => {
        try {
          const { data } = await shopApi.get(`/public/${empresaUrl}/orders/${id}`);
          byId.set(data.id, data);
        } catch { /* order may have been removed */ }
      })
    );
    const list = [...byId.values()].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    setOrders(list);
    setLoading(false);
  }, [customer, empresaUrl]);

  useEffect(() => {
    shopApi.get(`/public/${empresaUrl}`).then(({ data }) => setCompany(data.company)).catch(() => {});
  }, [empresaUrl]);

  useEffect(() => {
    if (authLoading) return;
    setLoading(true);
    load();
    const t = setInterval(load, 15000); // live status updates
    return () => clearInterval(t);
  }, [authLoading, load]);

  const active = useMemo(() => orders.filter((o) => ACTIVE(o.status)), [orders]);
  const past = useMemo(() => orders.filter((o) => !ACTIVE(o.status)), [orders]);

  return (
    <div className="store">
      <header className="orders-page-head">
        <div className="container store-topbar-inner" style={{ justifyContent: "space-between" }}>
          <Link to={`/${empresaUrl}`} className="center gap8" style={{ color: "#fff" }}>
            <img src={company?.logo_url || iconLogo} alt="" className="orders-head-logo" />
            <strong>{company?.name || "Loja"}</strong>
          </Link>
          {customer ? (
            <button className="acct-btn login" onClick={logout}>Sair</button>
          ) : (
            <button className="acct-btn login" onClick={() => setAuthModal(true)}>Entrar</button>
          )}
        </div>
      </header>

      <div className="container store-body" style={{ maxWidth: 720 }}>
        <div className="between">
          <h2>Meus pedidos</h2>
          <Link to={`/${empresaUrl}`} className="btn ghost sm">← Cardápio</Link>
        </div>

        {!customer && (
          <div className="login-suggest mt8">
            <strong>Entre na sua conta</strong>
            <p className="text-sm muted">
              {orders.length > 0
                ? "Você está vendo pedidos feitos neste dispositivo. Entre para ver todo o seu histórico nesta loja."
                : "Entre para ver o histórico de pedidos desta loja."}
            </p>
            <button className="btn sm" onClick={() => setAuthModal(true)}>Entrar / Criar conta</button>
          </div>
        )}

        {loading ? (
          <div className="spinner" />
        ) : orders.length === 0 ? (
          <div className="empty">
            Você ainda não fez pedidos nesta loja. 🍽️
            <div className="mt16"><button className="btn" onClick={() => navigate(`/${empresaUrl}`)}>Ver cardápio</button></div>
          </div>
        ) : (
          <div className="stack mt16">
            {active.length > 0 && (
              <>
                <h3 style={{ margin: 0 }}>Em andamento</h3>
                {active.map((o) => <OrderCard key={o.id} order={o} defaultOpen />)}
              </>
            )}
            {past.length > 0 && (
              <>
                <h3 style={{ margin: "10px 0 0" }}>Histórico</h3>
                {past.map((o) => <OrderCard key={o.id} order={o} />)}
              </>
            )}
          </div>
        )}
      </div>

      {authModal && <CustomerAuthModal onClose={() => setAuthModal(false)} onAuthed={load} />}
    </div>
  );
}
