import { Link } from "react-router-dom";
import logo from "../assets/yumi_logo.png";

export default function Home() {
  return (
    <div className="home">
      <header className="home-nav container">
        <img src={logo} alt="Yumi" className="home-logo" />
        <nav className="center gap12">
          <Link to="/login" className="btn ghost sm">Entrar</Link>
          <Link to="/register" className="btn sm">Criar loja</Link>
        </nav>
      </header>

      <main className="home-hero container">
        <div className="home-hero-text">
          <span className="badge orange">🍜 Delivery sem complicação</span>
          <h1>Seu cardápio digital, do jeito que o seu negócio merece.</h1>
          <p className="muted">
            Crie a loja da sua empresa, monte o cardápio com opções no estilo iFood,
            receba pedidos por <strong>entrega, retirada ou consumo no local</strong> e
            aceite <strong>PIX</strong> ou pagamento na entrega. Tudo em um link público
            só seu.
          </p>
          <div className="center gap12 mt16">
            <Link to="/register" className="btn lg">Começar agora — é grátis</Link>
            <Link to="/yumi-sushi" className="btn ghost lg">Ver loja demo</Link>
          </div>
        </div>
        <div className="home-hero-card card">
          <ul className="home-features">
            <li><span>🏪</span> Cadastro da empresa + login do admin</li>
            <li><span>🧾</span> Cardápio com categorias e itens</li>
            <li><span>🧩</span> Opções: escolha até N, repetir ou não</li>
            <li><span>🔗</span> Link público: <code>/sua-loja</code></li>
            <li><span>💳</span> PIX (copia e cola + QR) e pagar na entrega</li>
            <li><span>🕒</span> Horários, endereço e taxa de entrega</li>
          </ul>
        </div>
      </main>

      <footer className="home-footer container muted">
        Yumi · feito para deixar seu delivery delicioso de gerenciar.
      </footer>
    </div>
  );
}
