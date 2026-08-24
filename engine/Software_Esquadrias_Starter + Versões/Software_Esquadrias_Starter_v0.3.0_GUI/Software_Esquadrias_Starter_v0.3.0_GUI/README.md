# Software Esquadrias — CR Engine / Tester v0.3.0

## Principal mudança

A v0.3 separa:

1. **Consumo técnico** — o que efetivamente entra na esquadria.
2. **Compra de barras** — quantas barras inteiras de 5.900 mm precisam ser adquiridas.

A compra só é otimizada corretamente quando vários itens são reunidos no mesmo pedido.

## Executar

```powershell
python tester_gui.py
```

## Fluxo de teste

1. Configure uma esquadria.
2. Clique `CALCULAR ITEM`.
3. Clique `+ ADICIONAR AO PEDIDO`.
4. Repita para os demais itens do orçamento.
5. Abra `Compra de barras`.
6. Compare com `PED_P` do Excel.
7. Abra `Plano de corte` para conferir quais cortes foram encaixados em cada barra.

## Novo campo: Aplicação

`JANELA` e `PORTA` não são mais inferidos pelo tipo da folha.

Isso replica corretamente a coluna `I` da tabela `ORCS`.

## Algoritmo de barras

A versão usa **First Fit Decreasing (FFD)** com barra padrão de 5900 mm, reproduzindo o comportamento observado no Excel.

No pedido real enviado, 18/19 linhas do `PED_P` foram reproduzidas exatamente.

A única divergência é um erro do Excel:

`DE5013` possui 4 cortes de 1902 mm e precisa de 2 barras, mas o Excel registra 1.

## Teste real enviado

O pedido de teste possui 4 itens CR.

O `PED_P` legado totaliza:

`R$ 9.537,055`

Corrigindo o DE5013 para 2 barras:

`R$ 9.596,881`

A Engine v0.3 retorna:

`R$ 9.596,881`

## Arquitetura SaaS

O Tester Tkinter continua sendo apenas o laboratório local.

A Engine permanece desacoplada e poderá ser chamada futuramente por API/FastAPI.

O schema PostgreSQL v0.3 adiciona:
- políticas de compra por material;
- purchase_plans;
- purchase_plan_lines;
- cut_plan_bars;
- cut_plan_pieces;
- material_remnants.

Arquivo:

`db/schema_v0_3_saas.sql`
