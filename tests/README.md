# 🧪 Testes Automatizados (Yumi)

Esta pasta contém testes ponta a ponta (E2E) construídos utilizando **pytest** e **Playwright** para garantir o funcionamento correto dos fluxos principais da aplicação.

## 📋 Pré-requisitos

1. Python 3.8 ou superior instalado localmente.
2. A aplicação Yumi deve estar rodando (normalmente via Docker Compose na raiz do projeto):
   ```bash
   docker compose up -d
   ```

## ⚙️ Instalação das dependências de teste

Para instalar as dependências necessárias e baixar os binários dos navegadores utilizados pelo Playwright, execute:

```bash
# 1. Instalar pacotes python
pip install -r requirements-test.txt

# 2. Instalar os navegadores do Playwright
playwright install chromium
```

## 🚀 Execução dos testes

Para executar todos os testes automatizados com o navegador em background (modo headless):

```bash
pytest
```

### Comandos úteis adicionais:

*   **Ver a execução no navegador (modo headed)**:
    ```bash
    pytest --headed
    ```
*   **Rodar os testes em uma URL diferente** (por padrão aponta para `http://localhost:5173`):
    ```bash
    pytest --base-url http://meusite.com
    ```
*   **Atrasar a execução de cada ação** (útil em modo headed para assistir lentamente):
    ```bash
    pytest --headed --slowmo 1000
    ```
