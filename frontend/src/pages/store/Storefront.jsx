import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { shopApi } from "../../api";
import { formatBRL, WEEKDAYS, ORDER_TYPE_LABELS, waNumber } from "../../lib";
import { useCustomerAuth } from "../../customerAuth.jsx";
import iconLogo from "../../assets/yumi_icon.png";
import ProductModal from "./ProductModal.jsx";
import Checkout from "./Checkout.jsx";
import CustomerAuthModal from "./CustomerAuthModal.jsx";

export default function Storefront() {
  const { empresaUrl } = useParams();
  const navigate = useNavigate();
  const { customer, logout } = useCustomerAuth();
  const [store, setStore] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ok | notfound
  const [tab, setTab] = useState("menu");
  const [cart, setCart] = useState([]);
  const [product, setProduct] = useState(null);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [activeCat, setActiveCat] = useState(null);
  const [authModal, setAuthModal] = useState(false);
  const [acctOpen, setAcctOpen] = useState(false);
  const catRefs = useRef({});
  // Só fecha o drawer quando o clique COMEÇA no backdrop (não ao soltar fora
  // após selecionar texto num input do checkout).
  const pressedOnDrawerBackdrop = useRef(false);

  useEffect(() => {
    shopApi
      .get(`/public/${empresaUrl}`)
      .then(({ data }) => { setStore(data); setStatus("ok"); })
      .catch(() => setStatus("notfound"));
  }, [empresaUrl]);

  const cartCount = useMemo(() => cart.reduce((a, ci) => a + ci.quantity, 0), [cart]);
  const cartTotal = useMemo(() => cart.reduce((a, ci) => a + ci.unitPrice * ci.quantity, 0), [cart]);

  function scrollToCat(id) {
    setActiveCat(id);
    catRefs.current[id]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (status === "loading") return <div className="spinner" />;
  if (status === "notfound")
    return (
      <div className="store-notfound">
        <img src={iconLogo} alt="Yumi" width="80" />
        <h2>Loja não encontrada</h2>
        <p className="muted">O link <strong>/{empresaUrl}</strong> não existe ou foi alterado.</p>
        <Link to="/" className="btn">Voltar ao início</Link>
      </div>
    );

  const { company, categories, is_open_now } = store;
  const nonEmpty = categories.filter((c) => c.items.length > 0);

  return (
    <div className="store">
      {/* Account bar over the cover */}
      <div className="store-topbar">
        <div className="container store-topbar-inner">
          {customer ? (
            <div className="acct">
              <button className="acct-btn" onClick={() => setAcctOpen((o) => !o)}>
                <span className="acct-avatar">{customer.name.charAt(0).toUpperCase()}</span>
                <span className="acct-name">{customer.name.split(" ")[0]}</span>
                <span style={{ fontSize: 11 }}>▾</span>
              </button>
              {acctOpen && (
                <>
                  <div className="acct-overlay" onClick={() => setAcctOpen(false)} />
                  <div className="acct-menu">
                    <button onClick={() => { setAcctOpen(false); navigate(`/${empresaUrl}/pedidos`); }}>🧾 Meus pedidos</button>
                    <button onClick={() => { setAcctOpen(false); logout(); }}>🚪 Sair</button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button className="acct-btn login" onClick={() => setAuthModal(true)}>👤 Entrar</button>
          )}
        </div>
      </div>

      {/* Header */}
      <div className="store-cover" style={company.cover_url ? { backgroundImage: `url(${company.cover_url})` } : {}}>
        <div className="store-cover-overlay" />
      </div>
      <div className="store-header container">
        <div className="store-logo">
          {company.logo_url ? <img src={company.logo_url} alt={company.name} /> : <img src={iconLogo} alt="Yumi" />}
        </div>
        <div className="grow">
          <h1>{company.name}</h1>
          {company.description && <p className="muted">{company.description}</p>}
          <div className="store-meta">
            <span className={`badge ${is_open_now ? "green" : "red"}`}>
              {is_open_now ? "🟢 Aberto agora" : "🔴 Fechado"}
            </span>
            {company.estimated_time && <span className="badge gray">⏱ {company.estimated_time}</span>}
            {company.delivery_enabled && (
              <span className="badge gray">🛵 {company.delivery_fee > 0 ? formatBRL(company.delivery_fee) : "Grátis"}</span>
            )}
            {company.min_order_value > 0 && (
              <span className="badge gray">Mín. {formatBRL(company.min_order_value)}</span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="store-tabs container">
        <button className={`store-tab ${tab === "menu" ? "active" : ""}`} onClick={() => setTab("menu")}>Cardápio</button>
        <button className={`store-tab ${tab === "info" ? "active" : ""}`} onClick={() => setTab("info")}>Informações</button>
      </div>

      <div className="container store-body">
        {!is_open_now && tab === "menu" && (
          <div className="alert info">A loja está fechada no momento, mas você pode montar seu pedido. 😉</div>
        )}

        {tab === "menu" && (
          <>
            {nonEmpty.length > 1 && (
              <div className="cat-nav">
                {nonEmpty.map((c) => (
                  <button key={c.id} className={`pill ${activeCat === c.id ? "active" : ""}`} onClick={() => scrollToCat(c.id)}>
                    {c.name}
                  </button>
                ))}
              </div>
            )}

            {nonEmpty.length === 0 && <div className="empty">Esta loja ainda não cadastrou itens.</div>}

            {nonEmpty.map((cat) => (
              <section key={cat.id} ref={(el) => (catRefs.current[cat.id] = el)} className="store-cat">
                <h2>{cat.name}</h2>
                {cat.description && <p className="muted">{cat.description}</p>}
                <div className="product-grid">
                  {cat.items.map((item) => (
                    <button
                      key={item.id}
                      className={`product-card ${!item.is_available ? "disabled" : ""}`}
                      onClick={() => item.is_available && setProduct(item)}
                      disabled={!item.is_available}
                    >
                      <div className="product-card-info">
                        <strong>{item.name}</strong>
                        {item.description && <p className="muted text-sm">{item.description}</p>}
                        <span className="price">{formatBRL(item.base_price)}</span>
                        {!item.is_available && <span className="badge gray">Indisponível</span>}
                      </div>
                      <div className="product-card-thumb">
                        {item.image_url ? <img src={item.image_url} alt="" /> : <span>🍽️</span>}
                      </div>
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </>
        )}

        {tab === "info" && (
          <div className="store-info stack">
            <section className="card pad">
              <h3>Endereço</h3>
              {company.address_street ? (
                <p className="muted">
                  {company.address_street}, {company.address_number}
                  {company.address_complement && ` - ${company.address_complement}`}<br />
                  {company.address_neighborhood && `${company.address_neighborhood} · `}
                  {company.address_city}{company.address_state && ` - ${company.address_state}`}
                  {company.address_zip && <><br />CEP {company.address_zip}</>}
                </p>
              ) : <p className="muted">Endereço não informado.</p>}
              {(company.phone || company.whatsapp) && (
                <p className="muted">
                  {company.phone && <>📞 {company.phone}<br /></>}
                  {company.whatsapp && <a href={`https://wa.me/${waNumber(company.whatsapp)}`} target="_blank" rel="noreferrer">💬 WhatsApp</a>}
                </p>
              )}
            </section>

            <section className="card pad">
              <h3>Horários de funcionamento</h3>
              <div className="hours-table">
                {WEEKDAYS.map((day, i) => {
                  const h = (company.hours || []).find((x) => x.weekday === i);
                  return (
                    <div key={i} className="hours-line">
                      <span>{day}</span>
                      <span className="muted">
                        {!h || h.is_closed ? "Fechado" : `${h.open_time} - ${h.close_time}`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="card pad">
              <h3>Formas de recebimento e pagamento</h3>
              <div className="center gap8" style={{ flexWrap: "wrap" }}>
                {company.delivery_enabled && <span className="badge orange">🛵 {ORDER_TYPE_LABELS.delivery}</span>}
                {company.pickup_enabled && <span className="badge orange">🏪 {ORDER_TYPE_LABELS.pickup}</span>}
                {company.dine_in_enabled && <span className="badge orange">🍴 {ORDER_TYPE_LABELS.dine_in}</span>}
              </div>
              <div className="center gap8 mt8" style={{ flexWrap: "wrap" }}>
                {company.pix_enabled && <span className="badge green">💠 PIX</span>}
                {company.cash_enabled && <span className="badge green">💵 Pagar na entrega</span>}
              </div>
            </section>
          </div>
        )}
      </div>

      {/* Floating cart */}
      {cartCount > 0 && !checkoutOpen && (
        <button className="cart-fab" onClick={() => setCheckoutOpen(true)}>
          <span className="cart-fab-count">{cartCount}</span>
          <span>Ver carrinho</span>
          <span className="cart-fab-total">{formatBRL(cartTotal)}</span>
        </button>
      )}

      {product && (
        <ProductModal item={product} onClose={() => setProduct(null)} onAdd={(ci) => setCart((c) => [...c, ci])} />
      )}

      {checkoutOpen && (
        <div
          className="drawer-backdrop"
          onMouseDown={(e) => {
            pressedOnDrawerBackdrop.current = e.target === e.currentTarget;
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget && pressedOnDrawerBackdrop.current) setCheckoutOpen(false);
          }}
        >
          <div className="drawer">
            <Checkout
              company={company}
              cart={cart}
              setCart={setCart}
              onClose={() => setCheckoutOpen(false)}
              onTrackOrders={() => navigate(`/${empresaUrl}/pedidos`)}
            />
          </div>
        </div>
      )}

      {authModal && (
        <CustomerAuthModal onClose={() => setAuthModal(false)} />
      )}

      <footer className="store-footer">
        <a href="/" className="muted text-sm">Feito com <img src={iconLogo} width="16" style={{ verticalAlign: "middle" }} alt="Yumi" /> Yumi</a>
      </footer>
    </div>
  );
}
