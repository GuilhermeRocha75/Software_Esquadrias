# GR — Reverse engineering Fase 5

Status: **GR_ENGINE_0.5.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 5 adiciona portas GR Design 60x104 de **2 folhas**, abertura interna ou externa, painel completo, módulo único, fechamento monoponto ou multiponto.

A janela GR Design 60x78 permanece limitada a 1 folha.

## Evidência histórica

Foram encontrados 72 casos limpos de porta GR 2 folhas com painel completo no histórico ORCS. O histórico foi usado para identificar geometria, combinações e ferragens. Valores antigos de custo não são tratados automaticamente como preço corrente.

## Geometria do XLSM

Para largura total `W`, altura `H` e `G5=2` folhas:

- marco horizontal final: `W`;
- marco horizontal corte: `W + 5`;
- marco vertical final: `H`;
- marco vertical corte: `H + 3`;
- largura final de cada folha: `W/2 - 42`;
- largura de corte de cada folha: `W/2 - 37`;
- altura final de cada folha: `H - 37`;
- altura de corte de cada folha: `H - 32`;
- baguete/painel horizontal por folha: `largura_folha - 172`;
- baguete/painel vertical por folha: `altura_folha - 172`.

As peças de folha, baguetes e reforços são multiplicadas pelo número de folhas conforme as fórmulas da aba `GR`.

## LEGACY_BUG_CONFIRMED — painel DE20150

O XLSM calcula em `GR!G41` a quantidade vertical de faixas `DE20150`, porém em uma porta de 2 folhas **não multiplica essa quantidade por 2**.

Confirmação da fabricação em 2026-09-17:

> cada folha recebe seu próprio painel completo; em 2 folhas, a quantidade de painéis/faixas dobra.

Portanto a Engine usa:

`faixas_totais = faixas_por_folha * quantidade_de_folhas`

Classificação: **LEGACY_BUG_CONFIRMED**.

No golden 1600x2100:

- faixas por folha: `(1891 - 104) / 140 = 12,764285714...`;
- físico correto para 2 folhas: `25,528571428...`;
- diferença de custo em relação ao legado subcontado: **R$ 151,616994** com o catálogo atual.

## RESOLVED_PHYSICAL — calços AC0312

A fabricação confirmou:

- 4 calços `AC0312` por folha;
- função: manter a folha no esquadro e impedir que ceda, com ou sem vidro;
- porta 2 folhas: **8 calços no total**.

A Engine aplica `4 * quantidade_de_folhas`.

## RESOLVED_PHYSICAL — folha passiva

A fabricação confirmou que a folha passiva usa:

- `2x FEC7 — FECHO UNHA`;
- `2x CON3 — CONTRA FECHO UNHA`.

Os fechos vêm como **kit completo com seus próprios parafusos**. Não deve ser adicionada quantidade extra de `PAR1` para `FEC7/CON3`.

Isso coincide com o fato de a fórmula legada de `PAR1` não somar esses fechos; neste ponto o comportamento do Excel está fisicamente correto.

## Golden v0.5

Arquivo:

`test_cases/gr_golden_v0_5.json`

Caso congelado principal:

- porta 1600x2100;
- 2 folhas;
- abertura interna Design 60x104;
- painel completo;
- monoponto;
- custo técnico corrigido: **R$ 2.223,252898**.

Geometria principal:

- marco: 1600/1605 x 2100/2103 mm;
- cada folha: 758/763 x 2063/2068 mm;
- painel por folha: 586 x 1891 mm;
- faixas físicas totais: 25,528571;
- 8 calços AC0312;
- 6 dobradiças;
- folha passiva: 2 FEC7 + 2 CON3.

## Limites mantidos

A Fase 5 ainda não libera:

- janela de 2 folhas;
- vidro ou composição vidro/painel;
- tela;
- persiana;
- bandeiras;
- travessas;
- reforço estrutural opcional;
- plano de compra/corte GR.

Essas variantes continuam bloqueadas até evidência própria.

## Gate

CR `CR_ENGINE_0.5.0` e Maxim-Ar `MX_ENGINE_0.3.0` permanecem congelados. A Fase 5 só pode ser considerada pronta para homologação após CI completo de Engine + API + Web e auditoria independente.
