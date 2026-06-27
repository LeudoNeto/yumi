import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { apiError } from "../api";
import logo from "../assets/yumi_logo.png";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      navigate("/admin");
    } catch (err) {
      setError(apiError(err, "Não foi possível entrar."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card card">
        <Link to="/"><img src={logo} alt="Yumi" className="auth-logo" /></Link>
        <h2>Entrar na sua loja</h2>
        <p className="muted text-sm">Acesse o painel para gerenciar pedidos e cardápio.</p>
        {error && <div className="alert error mt16">{error}</div>}
        <form onSubmit={onSubmit} className="mt16">
          <div className="field">
            <label>E-mail</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </div>
          <div className="field">
            <label>Senha</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button className="btn block lg" disabled={busy}>
            {busy ? "Entrando..." : "Entrar"}
          </button>
        </form>
        <p className="text-sm muted mt16" style={{ textAlign: "center" }}>
          Ainda não tem loja? <Link to="/register">Criar agora</Link>
        </p>
      </div>
    </div>
  );
}
