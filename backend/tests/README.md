# 🧪 Testes Unitários e de Integração (Backend)

Este diretório contém os testes unitários e de integração do backend do **Yumi**, desenvolvidos com **pytest**.

Os testes utilizam um banco de dados SQLite em memória (`sqlite:///`) configurado de forma isolada e efêmera para cada execução, garantindo testes rápidos e sem necessidade de conexão com o banco MySQL de desenvolvimento.

---

## 🚀 Como Executar os Testes do Backend

### 🐳 Via Docker (Recomendado)
Com os contêineres do Docker ativos, execute o seguinte comando na raiz do projeto:
```bash
docker compose exec backend env PYTHONPATH=. pytest tests/ -v
```

### ⚙️ Execução Local (Sem Docker)
1. Certifique-se de ter as dependências instaladas na pasta `backend`:
   ```bash
   cd backend
   pip install -r requirements.txt -r requirements-test.txt
   ```
2. Defina a variável `PYTHONPATH` e execute o pytest:
   - **No Windows (PowerShell)**:
     ```powershell
     $env:PYTHONPATH="."
     pytest tests/ -v
     ```
   - **No Linux / macOS**:
     ```bash
     export PYTHONPATH=.
     pytest tests/ -v
     ```

---

## 📂 Estrutura dos Arquivos de Teste

Abaixo está a descrição simplificada do que cada arquivo de teste valida:

| Arquivo | Descrição |
| :--- | :--- |
| [conftest.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/conftest.py) | Configuração global do `pytest`, fixtures de banco de dados SQLite temporário, cliente de testes (`TestClient`) e geradores de dados mockados (como autenticação e cardápio base). |
| [test_auth_api.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_auth_api.py) | Valida fluxos de autenticação do administrador da loja (`/api/auth/*`), incluindo cadastro de conta, validação de e-mails/slugs duplicados e login. |
| [test_company_api.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_company_api.py) | Testa as operações de CRUD da empresa (`/api/company`), como alteração de nome, horário de funcionamento, configurações de taxa de entrega, métodos de pagamento e endereço. |
| [test_customer_api.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_customer_api.py) | Testa as rotas de clientes finais (`/api/customer/*`), incluindo fluxo de registro de conta do cliente, login, recuperação de dados do perfil (`/me`) e histórico/filtragem de pedidos. |
| [test_menu_api.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_menu_api.py) | Valida o gerenciamento do cardápio (`/api/menu/*`), englobando CRUD de categorias e itens (com grupos de opções) e controle de acesso cruzado (garantindo que um administrador não altere o cardápio de outra empresa). |
| [test_orders_api.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_orders_api.py) | Valida fluxos complexos de criação e gestão de pedidos, cobrando regras de negócio como valor mínimo, carrinho vazio, cálculo de taxas de entrega e preços com adicionais de opções, além do fluxo de alteração de status do pedido pelo painel administrativo. |
| [test_pix.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_pix.py) | Testa a utilidade de geração de payloads e QR Code PIX (padrão BACEN), validação do CRC16 e higienização de strings especiais. |
| [test_public_api.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_public_api.py) | Testa endpoints públicos acessados pelos clientes (`/api/public/*`), incluindo o cálculo e validação se a loja está aberta ou fechada com base em horários (inclusive para lojas que fecham após a meia-noite). |
| [test_schemas.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_schemas.py) | Valida os esquemas Pydantic (`schemas.py`), garantindo que validações de dados (como formatação de e-mails, senhas curtas, e quantidades positivas de itens) funcionem no nível do esquema. |
| [test_security.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_security.py) | Testa funções de hashing e verificação de senhas (bcrypt), bem como a correta codificação e decodificação de JSON Web Tokens (JWT) para admins e clientes. |
| [test_utils.py](file:///c:/Users/Luana/Downloads/yumi-main/yumi-main/backend/tests/test_utils.py) | Testa funções utilitárias do backend, como a geração automática de slugs seguros a partir do nome da loja (`slugify`) e validação da estrutura de slugs existentes. |
