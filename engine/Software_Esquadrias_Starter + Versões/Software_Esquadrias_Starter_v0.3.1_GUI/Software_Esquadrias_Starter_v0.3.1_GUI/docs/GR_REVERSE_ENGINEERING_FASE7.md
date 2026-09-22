# GR — Reverse engineering Fase 7

Status: **GR_ENGINE_0.7.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 7 adiciona **porta GR Design 60x104 com vidro inteiro e 2 folhas**, para abertura interna ou externa, preservando todo o escopo físico já homologado na Fase 6.

Escopo liberado de vidro após a Fase 7:

- aplicação: `PORTA`;
- folha: Design 60x104;
- abertura: interna ou externa;
- quantidade de folhas: 1 ou 2;
- preenchimento: `VIDRO INTEIRO`;
- módulo: único;
- fechamento: monoponto ou multiponto;
- sem tela, persiana, bandeiras, travessas ou reforço estrutural opcional.

A janela GR com vidro continua bloqueada.

## Fonte oficial

Workbook oficial:

`SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

O arquivo é usado somente como fonte de engenharia e não é versionado no repositório.

## Evidência histórica ORCS

Foram identificados **58 registros históricos utilizáveis de porta GR com 2 folhas e vidro**.

Distribuição principal observada:

- 41 com abertura interna;
- 17 com abertura externa;
- 47 com fechamento monoponto;
- 11 com fechamento multiponto;
- 27 com `06mm TEMPERADO INCOLOR`;
- 19 com `08mm TEMPERADO INCOLOR`.

Os registros são usados para validar geometria, composição do BOM e comportamento das fórmulas. Preços antigos não substituem automaticamente o catálogo atual.

## Caso de referência — ORCS 17138

Configuração:

- largura: 1200 mm;
- altura: 2100 mm;
- 2 folhas;
- abertura interna Design 60x104;
- vidro `06mm TEMPERADO INCOLOR`;
- fechamento monoponto.

### Geometria

Com `G5=2`:

- largura final de cada folha: `1200 / 2 - 42 = 558 mm`;
- altura final de cada folha: `2100 - 37 = 2063 mm`;
- vão de baguete por folha: `386 x 1891 mm`;
- vidro por folha: `378 x 1883 mm`;
- quantidade de vidros: 2;
- área de cada vidro: `0,711774 m²`;
- área total de vidro: `1,423548 m²`.

Para vidro 6 mm, `GR!B13` seleciona baguete `BA3518`.

## Paridade exata com o legado antes da correção física

Reconstruindo o BOM histórico com as fórmulas da aba GR e o catálogo correspondente, mas **sem as vedações que o Excel zera por bug**, o custo do ORCS 17138 é reproduzido exatamente:

**R$ 2.021,901650**

Esse valor coincide com o custo salvo no ORCS.

A paridade é importante porque comprova que a topologia de 2 folhas, baguetes, vidro, ferragens, calços e parafusos foi reconstruída corretamente antes de aplicar a correção física da Fase 6.

## GR!G118 — parafusos de reforço

A diferença de poucos centavos encontrada durante a auditoria foi resolvida sem arredondamento artificial.

`GR!G118` calcula `PAR2` sobre os **comprimentos de corte** usados nas linhas de marco e folha, e não sobre os comprimentos líquidos dos reforços.

Para ORCS 17138:

`PAR2 = 4 × ((1205 + 2103)/1000 + 4 × (563 + 2068)/1000)`

`PAR2 = 55,328 unidades`

Esse comportamento é preservado porque produz paridade exata com o legado e não contradiz nenhuma confirmação física existente.

## Regras físicas já confirmadas e reaproveitadas

### Calços

A fabricação confirmou que são utilizados **4 calços AC0312 por folha**, com ou sem vidro, para manter a folha no esquadro.

Porta de 2 folhas com vidro:

- `8x AC0312`.

### Folha passiva

A fabricação confirmou que a folha passiva usa:

- `2x FEC7 — FECHO UNHA`;
- `2x CON3 — CONTRA FECHO UNHA`.

Esses conjuntos já vêm com os próprios parafusos. Não é acrescentado `PAR1` extra por FEC7/CON3.

### Dobradiças

O recorte homologado utiliza `DOBRADIÇA 90MM`:

- 3 por folha;
- 6 em uma porta de 2 folhas.

### Vedações

Mantém-se a regra física confirmada em 2026-09-22:

- borracha de vidro/lambri no perímetro do preenchimento;
- borracha redonda na folha por fora;
- borracha redonda no marco por dentro.

Para ORCS 17138, a correção física acrescenta:

**R$ 49,943200**

Logo, o custo técnico físico da v0.7 é:

**R$ 2.071,844850**

Relação protegida por teste:

`2071,844850 - 49,943200 = 2021,901650`

## Ferragens e fechamento

No monoponto de 2 folhas permanecem:

- 6 dobradiças `DOB3`;
- 1 maçaneta dupla `MAC4`;
- 1 fechadura monoponto `FEC6`;
- 1 cilindro `CIL1`;
- 1 contra-testa `CON2`;
- 2 `FEC7`;
- 2 `CON3`;
- `PAR1 = 52`.

No multiponto, a folha passiva não muda e o delta contra o monoponto permanece exatamente **R$ 67,80**, pelas mesmas regras já auditadas na Fase 2.

## Golden v0.7

Arquivo:

`test_cases/gr_golden_v0_7.json`

O golden principal congela ORCS 17138 em duas visões simultâneas:

- custo legado reconstruído sem vedação: **R$ 2.021,901650**;
- custo físico corrigido v0.7: **R$ 2.071,844850**.

Também congela a regressão da porta de 1 folha com vidro e da porta de 2 folhas com painel.

## Arquitetura de versionamento

As versões anteriores continuam disponíveis como referência técnica:

- `gr.py` — v0.5, paridade legado antes da correção de vedação;
- `gr_v06.py` — v0.6, vedações físicas + vidro em porta de 1 folha;
- `gr_v07.py` — v0.7, adiciona vidro em porta de 2 folhas.

As suítes v0.5 e v0.6 importam explicitamente suas respectivas Engines, impedindo que um avanço de versão reescreva silenciosamente goldens históricos.

## Variantes ainda bloqueadas

### Janela GR com vidro

Permanece fora do escopo porque registros recentes apresentam variantes com `DOBRADIÇA SISTEMA OB` e ferragens diferentes do baseline de janela com painel. A ferragem não será inferida por analogia.

### Superior vidro / inferior painel

Há histórico relevante do modelo `SUPERIOR VIDRO/INFERIOR PAINEL`, porém a cota de divisão usada pelas fórmulas (`AC2` / Cota I) não está persistida de maneira suficientemente confiável em todos os registros ORCS analisados.

Essa variante exige uma regra explícita de altura de divisão antes de ser implementada.

### Outros limites

Continuam bloqueados:

- tela;
- persiana;
- bandeiras;
- travessas na folha;
- reforço estrutural opcional;
- plano de compra/corte GR.

## Gate

CR `CR_ENGINE_0.5.0` e Maxim-Ar `MX_ENGINE_0.3.0` permanecem congelados.

A Fase 7 só é considerada candidata tecnicamente válida após CI independente no SHA final, cobrindo:

1. regressão v0.5;
2. regressão v0.6;
3. golden e testes v0.7;
4. API;
5. Web build;
6. ausência de alterações internas de cálculo em CR/MX.
