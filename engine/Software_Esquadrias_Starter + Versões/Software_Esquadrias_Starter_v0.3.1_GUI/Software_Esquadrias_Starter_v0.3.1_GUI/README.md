# Software Esquadrias — Engineering Engine

## Maxim-Ar — Fase 2

A versão `MX_ENGINE_0.2.0` cobre de uma a oito folhas, horizontal/vertical,
tela recolhível e a matriz segura de bandeiras/módulos separados. Combinações
que o XLSM calcula de forma contraditória são rejeitadas, e a vedação DESIGN
continua pendente de homologação física. Os goldens v0.1 e v0.2 permanecem em
`test_cases/`; o fechamento está em
`docs/FECHAMENTO_TECNICO_MAXIM_AR_FASE2_2026-09-09.md` na raiz.

O CR permanece em `CR_ENGINE_0.5.0`.

## Fechamento CR — Fase 2

A Engine `CR_ENGINE_0.5.0` inclui o kit completo de persiana comprovado no
XLSM (`L2:M2:N2`), com perfis, talas, guias, eixo, acessórios, motores,
custos e cortes FFD. A tela de 3 folhas agora separa os dois quadros físicos
inteiros do fator legado de 1,5 usado apenas no consumo de malha.

As regras da Fase 1, o golden de R$ 8.317,53971, barra de 5.900 mm, kerf zero,
DE5013, travessas, bandeiras, reforços, cotas e vidros subdivididos permanecem
protegidos pela regressão. O relatório completo está em
`docs/FECHAMENTO_TECNICO_CR_FASE2_2026-09-08.md` na raiz do repositório.

## Fechamento CR — Fase 1

A Engine agora calcula grades de travessas nas folhas, painéis de vidro
dinâmicos, bandeiras inferior/superior, reforço estrutural e cotas livres por
vão. Esses componentes seguem até a BOM, custos, compra de barras e plano de
corte. A premissa formal de perda de serra é `kerf_mm = 0`.

O recorte simples anterior permanece num caminho de regressão compatível e o
golden continua em R$ 8.317,53971. A suíte atual possui 47 testes da Engine;
somada aos 5 testes da API, são 52 testes aprovados.

O marcador textual legado `CR` ainda depende de definição física para ser
importado; cotas numéricas explícitas já estão implementadas.

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

No pedido histórico consolidado, 18/19 linhas do `PED_P` foram reproduzidas exatamente.

A divergência observada nessa consolidação entre itens é um erro do Excel:

`DE5013` possui 4 cortes de 1902 mm e precisa de 2 barras, mas o Excel registra 1.

Esse alerta não se aplica ao caso unitário DESIGN 2000 × 2000 de 4 folhas:
nesse caso, o Excel e a Engine indicam corretamente 2 barras.

## Teste histórico enviado

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


## Ajustes da v0.3.1

- corrigido o grande espaço em branco acima das tabelas;
- as tabelas agora ocupam toda a área disponível das abas;
- `DT-CR-*` passou a ser apresentado como **informação de compatibilidade**;
- `LEGACY-*` passou a ser apresentado como **divergência/correção do Excel legado**;
- a aba de itens do pedido agora exibe largura e altura em colunas separadas, além do número de folhas;
- isso facilita conferir se o pedido digitado é realmente igual ao pedido usado no Excel.

### Diagnóstico do CSV enviado

O arquivo `plano_compra_perfis_v0_3.csv` possui:

- 335,244 m consumidos;
- 401,200 m comprados;
- 65,956 m de sobra;
- aproveitamento global aproximado de 83,56%;
- R$ 7.445,40 de custo por consumo dos materiais em barra;
- R$ 9.445,07 de desembolso pelas barras inteiras.

Ao cruzar o CSV com `PPED_P` do Excel de teste, encontramos indícios de diferença de entrada:
- o Excel contém uma PRIME 3500 × 2000 e uma PRIME 1500 × 3000;
- o plano da v0.3 corresponde a duas PRIME 1500 × 3000;
- a quantidade de acabamentos indica que um dos itens DESIGN foi lançado como PORTA, enquanto o Excel usa JANELA nos dois.

Portanto, essas diferenças devem ser corrigidas na entrada antes de julgar a equivalência do otimizador.
