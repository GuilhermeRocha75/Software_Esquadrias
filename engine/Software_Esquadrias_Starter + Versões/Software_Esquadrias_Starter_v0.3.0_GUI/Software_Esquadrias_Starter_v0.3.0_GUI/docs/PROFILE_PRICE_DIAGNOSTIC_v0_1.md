# Diagnóstico de preços de perfis — v0.1

## O que foi verificado

Os preços-base dos principais perfis usados pela CR Engine v0.2 foram comparados com a aba `LISTAPERFIS` do Excel fornecido.

| Código | Excel LISTAPERFIS (R$/m) | Engine v0.2 (R$/m) |
|---|---:|---:|
| PR8852 | 43,57 | 43,57 |
| PR13852 | 76,32 | 76,32 |
| PR4288 | 40,70 | 40,70 |
| PR4266 | 31,80 | 31,80 |
| PR4550 | 8,59 | 8,59 |
| PR4536 | 7,47 | 7,47 |
| DE16652 | 97,51 | 97,51 |
| DE60111 | 68,85 | 68,85 |
| AL16 | 4,10 | 4,10 |
| AL19 | 5,10 | 5,10 |

Portanto, para esses códigos, a divergência observada nos testes não é explicada pelo preço-base cadastrado.

## Como comparar corretamente

No Excel CR:

- coluna H = **valor unitário do material** (normalmente R$/m);
- coluna I = **valor total daquele componente na esquadria**.

No Tester v0.2.1:

- `Preço-base` = equivalente à coluna H;
- `Custo na esquadria` = equivalente conceitual à coluna I para uma unidade;
- `Custo total no pedido` = custo do componente multiplicado pela quantidade comercial.

## Onde procurar uma divergência

Para cada perfil divergente, conferir nesta ordem:

1. código do perfil selecionado;
2. preço-base por metro;
3. medida de corte em mm;
4. quantidade do perfil por esquadria;
5. custo total calculado para a linha.

A v0.2.1 inclui `Exportar BOM CSV (comparar com Excel)` para facilitar essa análise lado a lado.

## Próxima mudança arquitetural

Os preços ainda são um snapshot do Excel usado para construir a Engine. Na versão web/SaaS eles não ficarão hardcoded no código: cada empresa terá seu próprio catálogo e histórico de preços no PostgreSQL.
