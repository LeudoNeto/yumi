import { useState } from "react";
import Modal from "../../components/Modal.jsx";
import { apiError } from "../../api";
import { useCustomerAuth } from "../../customerAuth.jsx";
import iconLogo from "../../assets/yumi_icon.png";

export default function CustomerAuthModal({ onClose, onAuthed, initialMode = "login" }) {
  const { login, register } = useCustomerAuth();
  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        await login(form.email, form.password);
      } else {
        await register({
          name: form.name,
          email: form.email,
          phone: form.phone,
          password: form.password,
        });
      }
      onAuthed?.();
      onClose();
    } catch (err) {
      setError(apiError(err, "Não foi possível continuar."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={mode === "login" ? "Entrar" : "Criar conta"} onClose={onClose}>
      <div className="cust-auth-head">
        <img src={iconLogo} alt="" width="44" />
        <p className="muted text-sm">
          {mode === "login"
            ? "Acompanhe seus pedidos e agilize seu checkout."
            : "Crie sua conta para acompanhar pedidos e salvar seus dados."}
        </p>
      </div>

      <div className="seg" style={{ marginBottom: 14 }}>
        <button type="button" className={`seg-btn ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")}>Entrar</button>
        <button type="button" className={`seg-btn ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")}>Criar conta</button>
      </div>

      {error && <div className="alert error">{error}</div>}

      <form onSubmit={submit}>
        {mode === "register" && (
          <div className="field"><label>Nome</label>
            <input value={form.name} onChange={(e) => set("name", e.target.value)} required autoFocus /></div>
        )}
        <div className="field"><label>E-mail</label>
          <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required
            autoFocus={mode === "login"} /></div>
        {mode === "register" && (
          <div className="field"><label>Telefone / WhatsApp</label>
            <input value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="(11) 99999-9999" /></div>
        )}
        <div className="field"><label>Senha</label>
          <input type="password" value={form.password} minLength={6}
            onChange={(e) => set("password", e.target.value)} required /></div>
        <button className="btn block lg" disabled={busy}>
          {busy ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar conta"}
        </button>
      </form>
    </Modal>
  );
}
