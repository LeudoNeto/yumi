import { useEffect, useMemo, useState } from "react";
import { shopApi, apiError } from "../../api";
import { formatBRL, ORDER_TYPE_LABELS } from "../../lib";
import { useCustomerAuth } from "../../customerAuth.jsx";
import { rememberGuestOrder } from "./orderStore.js";
import PixView from "../../components/PixView.jsx";
import CustomerAuthModal from "./CustomerAuthModal.jsx";

export default function Checkout({ company, cart, setCart, onClose, onTrackOrders }) {
  const { customer } = useCustomerAuth();
  const availableTypes = [
    company.delivery_enabled && "delivery",
    company.pickup_enabled && "pickup",
    company.dine_in_enabled && "dine_in",
  ].filter(Boolean);

  const [step, setStep] = useState("cart"); // cart | checkout | done
  const [orderType, setOrderType] = useState(availableTypes[0] || "delivery");
  const [payment, setPayment] = useState(company.pix_enabled ? "pix" : "cash");
  const [authModal, setAuthModal] = useState(false);
  const [form, setForm] = useState({
    customer_name: "",
    customer_phone: "",
    address_street: "",
    address_number: "",
    address_complement: "",
    address_neighborhood: "",
    address_reference: "",
    table_number: "",
    notes: "",
    change_for: "",
  });
  const [placedOrder, setPlacedOrder] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  // prefill from the logged-in customer profile
  useEffect(() => {
    if (customer) {
      setForm((f) => ({
        ...f,
        customer_name: f.customer_name || customer.name || "",
        customer_phone: f.customer_phone || customer.phone || "",
      }));
    }
  }, [customer]);

  const subtotal = useMemo(
    () => cart.reduce((sum, ci) => sum + ci.unitPrice * ci.quantity, 0),
    [cart]
  );
  const deliveryFee = orderType === "delivery" ? company.delivery_fee : 0;
  const total = subtotal + deliveryFee;

  // payment options depend on order type (cash only for delivery)
  const paymentOptions = [
    company.pix_enabled && { key: "pix", label: "PIX" },
    company.cash_enabled && orderType === "delivery" && { key: "cash", label: "Pagar na entrega" },
  ].filter(Boolean);

  function changeType(t) {
    setOrderType(t);
    if (t !== "delivery" && payment === "cash") setPayment("pix");
  }

  function updateQty(uid, delta) {
    setCart((c) =>
      c
        .map((ci) => (ci.uid === uid ? { ...ci, quantity: ci.quantity + delta } : ci))
        .filter((ci) => ci.quantity > 0)
    );
  }
  function removeItem(uid) {
    setCart((c) => c.filter((ci) => ci.uid !== uid));
  }

  async function placeOrder() {
    setError("");
    if (!form.customer_name.trim() || !form.customer_phone.trim())
      return setError("Informe seu nome e telefone.");
    if (orderType === "delivery" && (!form.address_street.trim() || !form.address_number.trim()))
      return setError("Informe o endereço de entrega (rua e número).");
    if (company.min_order_value && subtotal < company.min_order_value)
      return setError(`O pedido mínimo é ${formatBRL(company.min_order_value)}.`);

    setBusy(true);
    try {
      const payload = {
        customer_name: form.customer_name,
        customer_phone: form.customer_phone,
        order_type: orderType,
        payment_method: payment,
        address_street: form.address_street,
        address_number: form.address_number,
        address_complement: form.address_complement,
        address_neighborhood: form.address_neighborhood,
        address_reference: form.address_reference,
        table_number: form.table_number,
        notes: form.notes,
        change_for: Number(form.change_for) || 0,
        items: cart.map((ci) => ({
          menu_item_id: ci.item.id,
          quantity: ci.quantity,
          notes: ci.notes,
          options: ci.selectedOptions.map((so) => ({ option_id: so.option.id, quantity: so.quantity })),
        })),
      };
      const { data } = await shopApi.post(`/public/${company.empresa_url}/orders`, payload);
      // remember locally so the order shows up in "Meus pedidos" even for guests
      rememberGuestOrder(company.empresa_url, data.id);
      setPlacedOrder(data);
      setStep("done");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  // ---------- DONE ----------
  if (step === "done" && placedOrder) {
    return (
      <div className="checkout-panel">
        <div className="checkout-done">
          <div className="done-check">✓</div>
          <h2>Pedido enviado!</h2>
          <p className="muted">Pedido <strong>#{placedOrder.id}</strong> · {ORDER_TYPE_LABELS[placedOrder.order_type]}</p>

          {placedOrder.payment_method === "pix" && placedOrder.pix_payload ? (
            <PixView payload={placedOrder.pix_payload} amount={placedOrder.total} />
          ) : (
            <div className="card pad" style={{ background: "var(--cream)", marginTop: 12 }}>
              <strong>Pagamento na entrega</strong>
              <p className="text-sm muted" style={{ margin: "6px 0 0" }}>
                Total a pagar: {formatBRL(placedOrder.total)}
                {placedOrder.change_for > 0 && ` · Troco para ${formatBRL(placedOrder.change_for)}`}
              </p>
            </div>
          )}

          {!customer && (
            <div className="login-suggest mt16">
              <strong>Crie uma conta para acompanhar este pedido</strong>
              <p className="text-sm muted">Salve seus dados e veja o histórico nesta loja.</p>
              <button className="btn sm block" onClick={() => setAuthModal(true)}>Criar conta / Entrar</button>
            </div>
          )}

          {company.whatsapp && (
            <a
              className="btn ghost block mt16"
              href={`https://wa.me/${company.whatsapp}?text=${encodeURIComponent(
                `Olá! Acabei de fazer o pedido #${placedOrder.id} (${formatBRL(placedOrder.total)}).`
              )}`}
              target="_blank" rel="noreferrer"
            >
              Enviar comprovante no WhatsApp
            </a>
          )}
          <button className="btn block mt16" onClick={() => { setCart([]); onClose(); onTrackOrders?.(); }}>
            Acompanhar pedido
          </button>
          <button className="btn ghost block mt8" onClick={() => { setCart([]); onClose(); }}>Voltar à loja</button>
        </div>
        {authModal && <CustomerAuthModal onClose={() => setAuthModal(false)} />}
      </div>
    );
  }

  // ---------- CART ----------
  if (step === "cart") {
    return (
      <div className="checkout-panel">
        <header className="checkout-head">
          <h2>Seu carrinho</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </header>
        <div className="checkout-scroll">
          {cart.length === 0 ? (
            <div className="empty">Seu carrinho está vazio. 🛒</div>
          ) : (
            cart.map((ci) => (
              <div key={ci.uid} className="cart-line">
                <div className="grow">
                  <strong>{ci.item.name}</strong>
                  {ci.selectedOptions.length > 0 && (
                    <div className="muted text-sm">
                      {ci.selectedOptions.map((so) =>
                        so.quantity > 1 ? `${so.quantity}× ${so.option.name}` : so.option.name
                      ).join(", ")}
                    </div>
                  )}
                  {ci.notes && <div className="muted text-sm">Obs.: {ci.notes}</div>}
                  <div className="price text-sm mt8">{formatBRL(ci.unitPrice * ci.quantity)}</div>
                </div>
                <div className="cart-line-actions">
                  <div className="qty-stepper sm">
                    <button onClick={() => updateQty(ci.uid, -1)}>−</button>
                    <span>{ci.quantity}</span>
                    <button onClick={() => updateQty(ci.uid, 1)}>+</button>
                  </div>
                  <button className="opt-remove" onClick={() => removeItem(ci.uid)}>remover</button>
                </div>
              </div>
            ))
          )}
        </div>
        <footer className="checkout-foot">
          <div className="between"><span className="muted">Subtotal</span><span className="price">{formatBRL(subtotal)}</span></div>
          {company.min_order_value > 0 && subtotal < company.min_order_value && (
            <div className="text-sm" style={{ color: "var(--red)" }}>
              Pedido mínimo: {formatBRL(company.min_order_value)}
            </div>
          )}
          <button className="btn block lg mt8" disabled={cart.length === 0} onClick={() => setStep("checkout")}>
            Continuar
          </button>
        </footer>
      </div>
    );
  }

  // ---------- CHECKOUT ----------
  return (
    <div className="checkout-panel">
      <header className="checkout-head">
        <button className="modal-close" onClick={() => setStep("cart")}>←</button>
        <h2>Finalizar pedido</h2>
        <button className="modal-close" onClick={onClose}>✕</button>
      </header>
      <div className="checkout-scroll">
        {error && <div className="alert error">{error}</div>}

        {customer ? (
          <div className="login-suggest ok">
            ✅ Pedido vinculado à sua conta — <strong>{customer.name}</strong>
          </div>
        ) : (
          <div className="login-suggest">
            <strong>Já tem conta?</strong>
            <p className="text-sm muted">Entre para preencher seus dados e acompanhar o pedido.</p>
            <div className="center gap8">
              <button className="btn sm" onClick={() => setAuthModal(true)}>Entrar / Criar conta</button>
              <span className="text-sm muted">ou continue como convidado</span>
            </div>
          </div>
        )}

        <h4>Como você quer receber?</h4>
        <div className="seg">
          {availableTypes.map((t) => (
            <button key={t} className={`seg-btn ${orderType === t ? "active" : ""}`} onClick={() => changeType(t)}>
              {ORDER_TYPE_LABELS[t]}
            </button>
          ))}
        </div>

        <div className="row mt16">
          <div className="field"><label>Nome</label>
            <input value={form.customer_name} onChange={(e) => set("customer_name", e.target.value)} required /></div>
          <div className="field"><label>Telefone</label>
            <input value={form.customer_phone} onChange={(e) => set("customer_phone", e.target.value)} required /></div>
        </div>

        {orderType === "delivery" && (
          <>
            <h4 className="mt16">Endereço de entrega</h4>
            <div className="row">
              <div className="field" style={{ flex: 3 }}><label>Rua</label>
                <input value={form.address_street} onChange={(e) => set("address_street", e.target.value)} /></div>
              <div className="field"><label>Número</label>
                <input value={form.address_number} onChange={(e) => set("address_number", e.target.value)} /></div>
            </div>
            <div className="row">
              <div className="field"><label>Complemento</label>
                <input value={form.address_complement} onChange={(e) => set("address_complement", e.target.value)} /></div>
              <div className="field"><label>Bairro</label>
                <input value={form.address_neighborhood} onChange={(e) => set("address_neighborhood", e.target.value)} /></div>
            </div>
            <div className="field"><label>Ponto de referência</label>
              <input value={form.address_reference} onChange={(e) => set("address_reference", e.target.value)} /></div>
          </>
        )}

        {orderType === "dine_in" && (
          <div className="field mt16"><label>Número da mesa (opcional)</label>
            <input value={form.table_number} onChange={(e) => set("table_number", e.target.value)} /></div>
        )}

        <h4 className="mt16">Pagamento</h4>
        <div className="seg">
          {paymentOptions.map((p) => (
            <button key={p.key} className={`seg-btn ${payment === p.key ? "active" : ""}`} onClick={() => setPayment(p.key)}>
              {p.label}
            </button>
          ))}
        </div>
        {payment === "cash" && (
          <div className="field mt8"><label>Precisa de troco para quanto? (opcional)</label>
            <input type="number" step="0.01" value={form.change_for} onChange={(e) => set("change_for", e.target.value)}
              placeholder="Deixe vazio se não precisar" /></div>
        )}
        {payment === "pix" && (
          <p className="text-sm muted">O QR Code e o código PIX serão gerados após confirmar o pedido.</p>
        )}

        <div className="field mt16"><label>Observações do pedido</label>
          <textarea value={form.notes} onChange={(e) => set("notes", e.target.value)} /></div>
      </div>

      <footer className="checkout-foot">
        <div className="between"><span className="muted">Subtotal</span><span>{formatBRL(subtotal)}</span></div>
        {deliveryFee > 0 && <div className="between"><span className="muted">Taxa de entrega</span><span>{formatBRL(deliveryFee)}</span></div>}
        <div className="between"><strong>Total</strong><strong className="price" style={{ fontSize: 18 }}>{formatBRL(total)}</strong></div>
        <button className="btn block lg mt8" disabled={busy} onClick={placeOrder}>
          {busy ? "Enviando..." : `Fazer pedido · ${formatBRL(total)}`}
        </button>
      </footer>
      {authModal && <CustomerAuthModal onClose={() => setAuthModal(false)} />}
    </div>
  );
}
