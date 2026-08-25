# API — Software Esquadrias

Esta pasta será a camada HTTP do Software Esquadrias.

## Objetivo inicial

Expor a Engine de cálculo através de uma API web, sem duplicar regras de engenharia.

Primeiros endpoints planejados:

- `GET /health`
- `POST /api/v1/engine/cr/calculate`
- `POST /api/v1/purchase-plans/calculate`

## Stack inicial

- Python
- FastAPI
- Pydantic
- Uvicorn

## Regra arquitetural

A API **não deve conter fórmulas de engenharia**. Ela valida entrada, chama a Engine e serializa a resposta.
