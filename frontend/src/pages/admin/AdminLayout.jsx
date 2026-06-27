import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth.jsx";
import api from "../../api";
import logo from "../../assets/yumi_icon.png";

export default function AdminLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    api.get("/company").then(({ data }) => setCompany(data)).catch(() => {});
  }, []);

  function doLogout() {
    logout();
    navigate("/login");
  }

  const links = [
    { to: "/admin/orders", label: "Pedidos", icon: "🧾" },
    { to: "/admin/menu", label: "Cardápio", icon: "🍽️" },
    { to: "/admin/settings", label: "Configurações", icon: "⚙️" },
  ];

  return (
    <div className="admin">
      <aside className={`admin-side ${menuOpen ? "open" : ""}`}>
        <div className="admin-brand">
          <img src={logo} alt="Yumi" />
          <div>
            <strong>{company?.name || "Yumi"}</strong>
            <span className="muted text-sm">Painel do admin</span>
          </div>
        </div>
        <nav className="admin-nav">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} onClick={() => setMenuOpen(false)}
              className={({ isActive }) => `admin-link ${isActive ? "active" : ""}`}>
              <span>{l.icon}</span> {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="admin-side-foot">
          {company && (
            <a href={`/${company.empresa_url}`} target="_blank" rel="noreferrer" className="btn ghost sm block">
              🔗 Ver loja pública
            </a>
          )}
          <button className="btn danger sm block mt8" onClick={doLogout}>Sair</button>
        </div>
      </aside>

      <div className="admin-main">
        <header className="admin-topbar">
          <button className="hamburger" onClick={() => setMenuOpen((o) => !o)}>☰</button>
          <img src={logo} alt="Yumi" className="topbar-logo" />
          <div className="grow" />
          {company && (
            <a href={`/${company.empresa_url}`} target="_blank" rel="noreferrer" className="btn ghost sm">
              Ver loja
            </a>
          )}
        </header>
        <main className="admin-content">
          <Outlet context={{ company, setCompany }} />
        </main>
      </div>
      {menuOpen && <div className="admin-overlay" onClick={() => setMenuOpen(false)} />}
    </div>
  );
}
