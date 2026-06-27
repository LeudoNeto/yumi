import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { apiError } from "../api";
import logo from "../assets/yumi_logo.png";

function slugify(v) {
  return v
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    company_name: "",
    empresa_url: "",
    admin_name: "",
    admin_email: "",
    password: "",
  });
  const [slugTouched, setSlugTouched] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function onCompanyName(v) {
    set("company_name", v);
    if (!slugTouched) set("empresa_url", slugify(v));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register({ ...form, empresa_url: slugify(form.empresa_url) });
      navigate("/admin");
    } catch (err) {
      setError(apiError(err, "Não foi possível criar a loja."));
    } finally {
      setBusy(false);
    }
  }

  const slug = slugify(form.empresa_url) || "sua-loja";

  return (
    <div className="auth-wrap">
      <div className="auth-card card wide">
        <Link to="/"><img src={logo} alt="Yumi" className="auth-logo" /></Link>
        <h2>Criar a loja da sua empresa</h2>
        <p className="muted text-sm">Cadastre a empresa e o acesso do administrador.</p>
        {error && <div className="alert error mt16">{error}</div>}
        <form onSubmit={onSubmit} className="mt16">
          <h4>Dados da empresa</h4>
          <div className="field">
            <label>Nome da empresa</label>
            <input value={form.company_name} onChange={(e) => onCompanyName(e.target.value)} required autoFocus />
          </div>
          <div className="field">
            <label>Link público (empresa_url)</label>
            <input
              value={form.empresa_url}
              onChange={(e) => { set("empresa_url", e.target.value); setSlugTouched(true); }}
              required
            />
            <div className="hint">Sua loja ficará em <strong>{location.origin}/{slug}</strong></div>
          </div>

          <h4 className="mt16">Acesso do administrador</h4>
          <div className="field">
            <label>Seu nome</label>
            <input value={form.admin_name} onChange={(e) => set("admin_name", e.target.value)} required />
          </div>
          <div className="row">
            <div className="field">
              <label>E-mail</label>
              <input type="email" value={form.admin_email} onChange={(e) => set("admin_email", e.target.value)} required />
            </div>
            <div className="field">
              <label>Senha</label>
              <input type="password" value={form.password} minLength={6} onChange={(e) => set("password", e.target.value)} required />
            </div>
          </div>
          <button className="btn block lg mt8" disabled={busy}>
            {busy ? "Criando..." : "Criar minha loja"}
          </button>
        </form>
        <p className="text-sm muted mt16" style={{ textAlign: "center" }}>
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </div>
  );
}
