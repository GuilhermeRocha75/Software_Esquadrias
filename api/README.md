# API — Software Esquadrias

Esta pasta é a camada HTTP do Software Esquadrias.

## Objetivo inicial

Expor a Engine de cálculo através de uma API web, sem duplicar regras de engenharia.

Endpoints já criados:

- `GET /health`
- `POST /api/v1/engine/cr/calculate`
- `POST /api/v1/purchase-plans/calculate`

A resposta do cálculo CR já inclui:

- geometria;
- BOM;
- `cost_by_group`;
- custo técnico unitário;
- custo técnico do pedido;
- alertas;
- versão da Engine.
- vãos e travessas estruturados;
- bandeiras inferior/superior;
- lista dinâmica de painéis de vidro;
- premissa de perda de serra (`kerf_mm`, padrão 0).

## Stack inicial

- Python
- FastAPI
- Pydantic
- Uvicorn

## Executar localmente

A partir da raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r api\requirements.txt
uvicorn api.app.main:app --reload
```

Depois acesse a documentação automática do FastAPI em:

```text
http://127.0.0.1:8000/docs
```

## Regra arquitetural

A API **não deve conter fórmulas de engenharia**. Ela valida entrada, chama a Engine e serializa a resposta.

### Ponte temporária

A API v0.1 ainda importa a Engine CR v0.4.0 a partir do diretório histórico v0.3.1 em `engine/`.

Isso é temporário. A próxima refatoração deve promover a Engine validada para um caminho estável (`engine/current` ou pacote equivalente), sem apagar o histórico das versões anteriores.
