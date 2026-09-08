# Web — Software Esquadrias

Primeira interface web funcional do projeto, construída em React + Vite e conectada à API FastAPI.

## O que já funciona

- tela principal de Novo Cliente / Orçamento;
- dados do cliente e da obra;
- lista de itens do orçamento;
- botão para inserir um modelo Correr;
- cálculo do pedido pela API;
- resumo com custo técnico, compra de barras, materiais não lineares e compra estimada;
- margem editável e preço de venda sugerido;
- indicadores de itens, alertas, aproveitamento e quantidade de barras;
- abas Custo por Grupo, BOM / Consumo, Compra de Barras, Plano de Corte e Alertas;
- persistência local do orçamento e itens via `localStorage` enquanto o banco ainda não está conectado.

## Executar localmente

### 1. API

Na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --reload
```

API: `http://127.0.0.1:8000`

### 2. Web

Em outro PowerShell:

```powershell
cd web
npm install
npm run dev
```

Web: `http://127.0.0.1:5173`

A API v0.1.2 já permite CORS para `127.0.0.1:5173` e `localhost:5173`.

## Arquitetura

A interface não contém fórmulas de engenharia. Ela envia a configuração para a API e apresenta o retorno da Engine.

Fluxo atual:

`React/Vite → FastAPI → Engine CR → plano de compra`

## Próximas funções planejadas

- Login e multiempresa;
- banco PostgreSQL;
- clientes e obras persistidos;
- salvar e versionar orçamentos;
- editar itens existentes;
- modelos Maxim-Ar, Giro, Fixo, Pivotante e Grade;
- item manual;
- substituição manual de valor;
- PDFs de orçamento;
- permissões por usuário.
