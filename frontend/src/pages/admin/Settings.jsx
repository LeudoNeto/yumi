import { useEffect, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import api, { apiError } from "../../api";
import { WEEKDAYS } from "../../lib";
import { MoneyInput, PhoneInput } from "../../components/Inputs.jsx";

const EMPTY_HOURS = WEEKDAYS.map((_, i) => ({
  weekday: i,
  is_closed: false,
  open_time: "09:00",
  close_time: "22:00",
}));

export default function Settings() {
  const { setCompany } = useOutletContext();
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);
  const logoInput = useRef();

  useEffect(() => {
    api.get("/company").then(({ data }) => {
      const hoursByDay = {};
      (data.hours || []).forEach((h) => (hoursByDay[h.weekday] = h));
      data.hours = EMPTY_HOURS.map((d) => hoursByDay[d.weekday] || d);
      setForm(data);
    });
  }, []);

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }
  function setHour(i, key, value) {
    setForm((f) => {
      const hours = f.hours.map((h, idx) => (idx === i ? { ...h, [key]: value } : h));
      return { ...f, hours };
    });
  }

  async function uploadLogo(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/company/logo", fd);
      set("logo_url", data.logo_url);
      setCompany(data);
    } catch (err) {
      setError(apiError(err));
    }
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setOk(false);
    try {
      const payload = {
        name: form.name,
        empresa_url: form.empresa_url,
        description: form.description,
        phone: form.phone,
        whatsapp: form.whatsapp,
        address_street: form.address_street,
        address_number: form.address_number,
        address_complement: form.address_complement,
        address_neighborhood: form.address_neighborhood,
        address_city: form.address_city,
        address_state: form.address_state,
        address_zip: form.address_zip,
        delivery_enabled: form.delivery_enabled,
        pickup_enabled: form.pickup_enabled,
        dine_in_enabled: form.dine_in_enabled,
        delivery_fee: Number(form.delivery_fee) || 0,
        min_order_value: Number(form.min_order_value) || 0,
        estimated_time: form.estimated_time,
        pix_enabled: form.pix_enabled,
        cash_enabled: form.cash_enabled,
        pix_key: form.pix_key,
        pix_merchant_name: form.pix_merchant_name,
        pix_merchant_city: form.pix_merchant_city,
        hours: form.hours.map((h) => ({
          weekday: h.weekday,
          is_closed: h.is_closed,
          open_time: h.open_time,
          close_time: h.close_time,
        })),
      };
      const { data } = await api.patch("/company", payload);
      setCompany(data);
      setOk(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(apiError(err));
    } finally {
      setSaving(false);
    }
  }

  if (!form) return <div className="spinner" />;

  return (
    <form onSubmit={save} className="stack" style={{ maxWidth: 820 }}>
      <div className="between">
        <h2>Configurações da loja</h2>
        <button className="btn" disabled={saving}>{saving ? "Salvando..." : "Salvar alterações"}</button>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert info">Alterações salvas com sucesso! ✅</div>}

      <section className="card pad">
        <h3>Identidade</h3>
        <div className="logo-row">
          <div className="logo-preview">
            {form.logo_url ? <img src={form.logo_url} alt="logo" /> : <span className="muted">Sem logo</span>}
          </div>
          <div>
            <button type="button" className="btn ghost sm" onClick={() => logoInput.current.click()}>
              Enviar logo
            </button>
            <input ref={logoInput} type="file" accept="image/*" hidden onChange={uploadLogo} />
            <div className="hint mt8">PNG, JPG ou WEBP até 5MB.</div>
          </div>
        </div>
        <div className="field mt16">
          <label>Nome da empresa</label>
          <input value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </div>
        <div className="field">
          <label>Link público (empresa_url)</label>
          <input value={form.empresa_url} onChange={(e) => set("empresa_url", e.target.value)} required />
          <div className="hint">{location.origin}/{form.empresa_url}</div>
        </div>
        <div className="field">
          <label>Descrição</label>
          <textarea value={form.description} onChange={(e) => set("description", e.target.value)} placeholder="Conte um pouco sobre a sua loja..." />
        </div>
        <div className="row">
          <div className="field"><label>Telefone</label>
            <PhoneInput value={form.phone} onChange={(v) => set("phone", v)} placeholder="(11) 98888-7777" /></div>
          <div className="field"><label>WhatsApp</label>
            <PhoneInput value={form.whatsapp} onChange={(v) => set("whatsapp", v)} placeholder="(11) 98888-7777" />
            <div className="hint">Adicionamos o +55 automaticamente nos links.</div></div>
        </div>
      </section>

      <section className="card pad">
        <h3>Endereço</h3>
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
        <div className="row">
          <div className="field" style={{ flex: 2 }}><label>Cidade</label>
            <input value={form.address_city} onChange={(e) => set("address_city", e.target.value)} /></div>
          <div className="field"><label>UF</label>
            <input value={form.address_state} maxLength={2} onChange={(e) => set("address_state", e.target.value)} /></div>
          <div className="field"><label>CEP</label>
            <input value={form.address_zip} onChange={(e) => set("address_zip", e.target.value)} /></div>
        </div>
      </section>

      <section className="card pad">
        <h3>Horários de funcionamento</h3>
        <div className="stack" style={{ gap: 8 }}>
          {form.hours.map((h, i) => (
            <div key={i} className="hours-row">
              <span className="hours-day">{WEEKDAYS[i]}</span>
              <label className="checkbox">
                <input type="checkbox" checked={!h.is_closed}
                  onChange={(e) => setHour(i, "is_closed", !e.target.checked)} />
                Aberto
              </label>
              <input type="time" value={h.open_time} disabled={h.is_closed}
                onChange={(e) => setHour(i, "open_time", e.target.value)} />
              <span className="muted">até</span>
              <input type="time" value={h.close_time} disabled={h.is_closed}
                onChange={(e) => setHour(i, "close_time", e.target.value)} />
            </div>
          ))}
        </div>
      </section>

      <section className="card pad">
        <h3>Formas de recebimento</h3>
        <div className="stack" style={{ gap: 10 }}>
          <label className="checkbox"><input type="checkbox" checked={form.delivery_enabled}
            onChange={(e) => set("delivery_enabled", e.target.checked)} /> 🛵 Entrega (delivery)</label>
          <label className="checkbox"><input type="checkbox" checked={form.pickup_enabled}
            onChange={(e) => set("pickup_enabled", e.target.checked)} /> 🏪 Retirar no estabelecimento</label>
          <label className="checkbox"><input type="checkbox" checked={form.dine_in_enabled}
            onChange={(e) => set("dine_in_enabled", e.target.checked)} /> 🍴 Consumir no local</label>
        </div>
        <div className="row mt16">
          <div className="field"><label>Taxa de entrega</label>
            <MoneyInput value={form.delivery_fee} onChange={(v) => set("delivery_fee", v)} /></div>
          <div className="field"><label>Pedido mínimo</label>
            <MoneyInput value={form.min_order_value} onChange={(v) => set("min_order_value", v)} /></div>
          <div className="field"><label>Tempo estimado</label>
            <input value={form.estimated_time} onChange={(e) => set("estimated_time", e.target.value)} placeholder="30-45 min" /></div>
        </div>
      </section>

      <section className="card pad">
        <h3>Pagamento</h3>
        <div className="stack" style={{ gap: 10 }}>
          <label className="checkbox"><input type="checkbox" checked={form.pix_enabled}
            onChange={(e) => set("pix_enabled", e.target.checked)} /> 💠 Aceitar PIX</label>
          <label className="checkbox"><input type="checkbox" checked={form.cash_enabled}
            onChange={(e) => set("cash_enabled", e.target.checked)} /> 💵 Pagar na entrega (dinheiro/cartão na hora)</label>
        </div>
        {form.pix_enabled && (
          <div className="mt16">
            <div className="field"><label>Chave PIX</label>
              <input value={form.pix_key} onChange={(e) => set("pix_key", e.target.value)}
                placeholder="e-mail, CPF/CNPJ, telefone ou chave aleatória" /></div>
            <div className="row">
              <div className="field"><label>Nome do recebedor (PIX)</label>
                <input value={form.pix_merchant_name} maxLength={25}
                  onChange={(e) => set("pix_merchant_name", e.target.value)} /></div>
              <div className="field"><label>Cidade do recebedor</label>
                <input value={form.pix_merchant_city} maxLength={15}
                  onChange={(e) => set("pix_merchant_city", e.target.value)} /></div>
            </div>
            <div className="hint">Usado para gerar o PIX Copia e Cola e o QR Code dos pedidos.</div>
          </div>
        )}
      </section>

      <div className="between">
        <span className="muted text-sm">As alterações valem imediatamente na loja pública.</span>
        <button className="btn lg" disabled={saving}>{saving ? "Salvando..." : "Salvar alterações"}</button>
      </div>
    </form>
  );
}
