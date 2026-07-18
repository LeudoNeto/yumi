# 🍜 Yumi — Web App de Delivery

Yumi é um web app de delivery multi-loja. Cada empresa cria sua conta, monta o
cardápio (no estilo iFood, com opções) e ganha um **link público** próprio
(`/{empresa_url}`) onde os clientes fazem pedidos — para **entrega**, **retirada**
ou **consumo no local** — pagando com **PIX** ou **na entrega**.

- **Front-end:** React + Vite + React Router
- **Back-end:** FastAPI (Python)
- **Banco de dados:** MySQL 8
- **Infra:** front-end, backend e banco rodam via **Docker Compose**

---

## ✨ Funcionalidades

1. **Cadastro da empresa** junto com o login do administrador.
2. **Painel do admin** (após login) para editar:
   - Dados da empresa: logo, `empresa_url` (link público), descrição, endereço,
     telefone/WhatsApp, **horários de funcionamento**, taxa de entrega, pedido
     mínimo, tempo estimado e formas de pagamento.
   - **Cardápio**: categorias e itens.
3. **Itens no padrão iFood**: preço base + **seções de opções**, cada seção com:
   - mínimo e **máximo de escolhas** (até N);
   - flag "**pode escolher a mesma opção mais de uma vez**" (quantidade por opção).
4. **Loja pública** em `dominio/{empresa_url}/` (sem login):
   - cardápio + aba de **Informações** (endereço, horários, pagamento);
   - carrinho e fechamento de pedido com **entrega / retirada / consumo no local**.
5. **Pagamento**: **PIX** (gera *Copia e Cola* + QR Code, padrão BACEN, sem gateway
   externo) ou **pagar na entrega** (apenas para delivery).
6. **Conta do cliente final** (separada da do admin):
   - botão **Entrar / Criar conta** no topo da loja pública;
   - sugestão de login/cadastro **no checkout** (mantendo o checkout como convidado);
   - tela **Meus pedidos** (`/{empresa_url}/pedidos`) com **histórico daquela loja** e
     **acompanhamento do pedido atual** (status ao vivo, atualizado a cada 15s);
   - pedidos de convidado também aparecem (rastreados pelo dispositivo) e os de quem
     está logado ficam vinculados à conta.

---

## 🚀 Como rodar

### Pré-requisitos
- Docker + Docker Compose
- Node.js 18+ (opcional — só para o modo de desenvolvimento do front-end)

### 1) Subir tudo (Docker Compose)

Na raiz do projeto:

```bash
docker compose up -d --build
```

Isso sobe:
- **MySQL** em `localhost:3306` (banco `yumi`, usuário `yumi` / senha `yumipass`)
- **API FastAPI** em `http://localhost:8000` (docs em `http://localhost:8000/docs`)
- **Front-end** (build do Vite servido por **nginx alpine**) em **http://localhost:5173**

O nginx serve o `dist/` do front e faz proxy de `/api` e `/uploads` para o backend —
como tudo fica na mesma origem, não há CORS envolvido.

O backend espera o MySQL ficar saudável e cria as tabelas automaticamente no start.

> As configurações têm padrões que funcionam de imediato. Para customizar (senhas,
> portas, chave secreta), copie `.env.example` para `.env`.

### 2) (Opcional) Popular com dados de demonstração

```bash
docker compose exec backend python seed.py
```

Cria uma loja demo:
- **Loja pública:** http://localhost:5173/yumi-sushi
- **Login admin:** `admin@yumi.com` / `yumi1234`

### 3) (Opcional) Front-end em modo de desenvolvimento

O container `frontend` já entrega o front pronto. Para hot-reload durante o
desenvolvimento, rode o Vite localmente — de preferência com o container `frontend`
parado (`docker compose stop frontend`) para não disputar a porta 5173:

```bash
cd frontend
npm install
npm run dev
```

App em **http://localhost:5173**. O Vite faz proxy de `/api` e `/uploads` para o
backend, então não há configuração extra de CORS para o dev.

---

## 🗺️ Rotas principais (front-end)

| Rota | Descrição |
|------|-----------|
| `/` | Landing page |
| `/register` | Cadastro de empresa + admin |
| `/login` | Login do admin |
| `/admin/orders` | Pedidos (com mudança de status) |
| `/admin/menu` | Editor de cardápio (categorias, itens, opções) |
| `/admin/settings` | Configurações da loja |
| `/:empresa_url` | **Loja pública** (cardápio, informações, carrinho, checkout) |
| `/:empresa_url/pedidos` | **Meus pedidos** do cliente (histórico + acompanhamento) |

---

## 🧱 Estrutura

```
yumi/
├── docker-compose.yml        # MySQL + backend + frontend (nginx)
├── .env.example              # variáveis do compose
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── seed.py               # dados de demonstração
│   └── app/
│       ├── main.py           # FastAPI app (CORS, static, routers, lifespan)
│       ├── config.py         # settings (pydantic-settings)
│       ├── database.py       # engine + init_db (espera o MySQL)
│       ├── models.py         # SQLAlchemy models
│       ├── schemas.py        # Pydantic schemas
│       ├── security.py       # bcrypt + JWT
│       ├── pix.py            # gera o BR Code / PIX Copia e Cola (CRC16)
│       ├── deps.py           # dependência de usuário autenticado
│       └── routers/          # auth, company, menu, public, orders
└── frontend/
    ├── Dockerfile            # build do Vite + nginx alpine (produção)
    ├── nginx.conf            # SPA + proxy /api e /uploads -> backend:8000
    ├── vite.config.js        # proxy /api e /uploads -> :8000 (dev)
    └── src/
        ├── api.js, auth.jsx, lib.js
        ├── pages/            # Home, Login, Register, admin/*, store/*
        └── components/       # Modal, ItemEditor, ProductModal, PixView
```

---

## 🔌 Principais endpoints da API

- `POST /api/auth/register` — cria empresa + admin, retorna JWT
- `POST /api/auth/login-json` — login do admin (JSON), retorna JWT
- `POST /api/customer/auth/register` · `POST /api/customer/auth/login` — conta do cliente
- `GET /api/customer/orders?empresa_url=...` — pedidos do cliente naquela loja
- `GET /api/public/{empresa_url}/orders/{id}` — rastrear um pedido (convidado)
- `GET/PATCH /api/company` — dados da loja (admin)
- `POST /api/company/logo` — upload da logo (admin)
- `GET/POST/PATCH/DELETE /api/menu/...` — categorias e itens (admin)
- `GET /api/public/{empresa_url}` — loja pública (cardápio + status aberto/fechado)
- `POST /api/public/{empresa_url}/orders` — cria pedido (público, calcula preços
  no servidor e gera o PIX)
- `GET /api/orders` · `PATCH /api/orders/{id}/status` — pedidos (admin)

---

## 💳 Sobre o PIX

O PIX é gerado **localmente** no padrão EMV-MPM do Banco Central (com CRC16), a
partir da chave PIX configurada na loja. O cliente recebe o **Copia e Cola** e o
**QR Code** ao finalizar o pedido — sem necessidade de gateway de pagamento.
Para produção real, integre a confirmação de pagamento a um provedor PIX.

---

## ⚠️ Notas de produção

- Defina um `SECRET_KEY` forte e troque as senhas do MySQL no `.env`.
- O front já vai para produção como build estático servido pelo **nginx** (serviço
  `frontend`), que também faz proxy de `/api` e `/uploads` para o backend. Como front
  e API ficam na mesma origem, o `CORS_ORIGINS` do backend só é necessário para o
  modo de desenvolvimento (Vite).
- Coloque o serviço `frontend` atrás de um proxy reverso com TLS (HTTPS) e ajuste
  `FRONTEND_PORT` / `PUBLIC_BASE_URL` conforme o domínio.
- Os uploads ficam em um volume Docker (`backend_uploads`).
