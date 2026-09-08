# Divergência legado CR — PAR2 / parafuso negativo

## Resumo

Foi identificada uma divergência sistemática de **R$ 0,08 por esquadria** entre o Excel legado e a Engine em casos CR sem bandeira inferior/superior.

## Fórmula do Excel

No CR legado, a quantidade de parafusos de reforço usa também `D37+D38+D43+D44`.

Quando não existe bandeira, `AA2=0` e `AB2=0`, mas as fórmulas de `D38` e `D44` retornam `-50` em vez de `0`.

Assim, o termo adicional equivale a:

`((0 - 50 + 0 - 50) / 1000) * 2 * 4 = -0,8`

Como o material `PAR2` custa R$ 0,10/un., o Excel reduz artificialmente o custo em:

`0,8 × R$ 0,10 = R$ 0,08`

por esquadria.

## Decisão recomendada

A Engine **não deve reproduzir quantidade negativa de parafuso**. O cálculo físico corrigido fica R$ 0,08/un. acima do Excel nesses casos.

Para comparações Excel × Engine, registrar a divergência como correção de legado, de forma semelhante ao tratamento já adotado para inconsistências comprovadas.

## Caso de referência 25/08/2026

Pedido com quatro itens CR sem bandeiras:

- total técnico Excel: **R$ 8.317,21971**;
- correção total: `4 × R$ 0,08 = R$ 0,32`;
- total técnico físico esperado da Engine: **R$ 8.317,53971**.
