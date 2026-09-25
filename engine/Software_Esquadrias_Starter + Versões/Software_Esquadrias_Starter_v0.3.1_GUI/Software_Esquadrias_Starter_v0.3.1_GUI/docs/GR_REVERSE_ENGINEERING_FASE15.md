# GR — Reverse engineering Fase 15

Status: **GR_ENGINE_0.15.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 15 inicia a expansão de bandeiras/fixos integrados da família GR com o recorte mais limpo do histórico:

- bandeira superior simples;
- porta GR Design 60x104;
- 1 folha;
- abertura interna ou externa;
- VIDRO INTEIRO;
- dobradiça 90 mm;
- fechamento monoponto ou multiponto;
- módulo único;
- sem divisões internas na bandeira;
- sem tela;
- sem persiana;
- sem reforço estrutural opcional.

Bandeira inferior, bandeira superior + inferior, subdivisões internas, 2 folhas e combinações com tela/persiana permanecem para fases seguintes.

## Evidência ORCS

Existem **46 registros GR** com altura de bandeira inferior e/ou superior preenchida.

A Fase 15 congela dois casos simples e reproduzíveis:

### ORCS 14891

- 1200x2700 mm;
- porta 1 folha;
- abertura interna;
- bandeira superior 600 mm;
- vidro 8 mm temperado incolor;
- monoponto;
- dobradiça 90 mm.

### ORCS 11251

- 1100x2700 mm;
- porta 1 folha;
- abertura externa;
- bandeira superior 600 mm;
- vidro 8 mm temperado incolor;
- monoponto;
- dobradiça 90 mm.

Os custos AO históricos são usados apenas como evidência da configuração. O golden atual usa catálogo vigente e as correções físicas já homologadas de vedações.

## Geometria do conjunto integrado

Para porta com uma bandeira superior em módulo único:

- o marco externo mantém a altura total da esquadria;
- a folha perde a altura ocupada pela bandeira e pela travessa de separação;
- a travessa de limite da bandeira é DE6072;
- o reforço da travessa é RAG - DE6072.

A fórmula GR da folha, com bandeira superior, resulta em:

`altura_folha = H_total - H_bandeira - 15`

Para largura de porta com uma folha:

`largura_folha = W - 64`

A travessa de limite usa:

`comprimento_DE6072 = W - 68`

## Abertura física da bandeira

A aba GR tenta montar a bandeira em GR!26:30, porém GR!26/28 referencia `LISTAPERFIS!E40`.

No workbook oficial, essa referência não fornece a dimensão necessária para a abertura fixa.

A família Maxim-Ar Design já homologada usa a mesma topologia física:

- marco DE6058;
- travessa DE6072;
- face do marco = 40 mm;
- profundidade da travessa = 18 mm.

A abertura física simples, sem subdivisões, é portanto:

`largura_vão = W - 80`

`altura_vão = H_bandeira - 58`

O vidro recebe o mesmo desconto de 8 mm já homologado:

`largura_vidro = W - 88`

`altura_vidro = H_bandeira - 66`

Classificação da referência GR quebrada:

**LEGACY_BUG_CONFIRMED_BY_SHARED_TOPOLOGY**

A recuperação não usa conhecimento externo; usa a própria topologia Design DE6058 + DE6072 já homologada no mesmo software.

## Baguete, vidro e vedação

A bandeira usa:

- a mesma seleção de baguete pela espessura do vidro;
- o mesmo vidro informado para o conjunto;
- borracha de vidro/lambri ACB606 no perímetro do vão fixo.

A confirmação física anterior das vedações GR permanece válida.

Não é adicionada borracha redonda de folha/marco à bandeira, pois o fixo não possui folha móvel.

## Reforços e parafusos

A travessa DE6072 recebe:

- RAG - DE6072;
- inclusão no cálculo de PAR2 do conjunto integrado.

O marco passa a possuir três segmentos horizontais estruturais no módulo:

- base;
- travessa superior externa;
- limite da bandeira.

A Engine preserva o custo por BOM e a rastreabilidade por papel de cada peça.

## Golden ORCS 14891 — abertura interna

Geometria:

- marco: 1200x2700 mm;
- folha: 1136x2085 mm;
- vidro principal: 956x1905 mm;
- travessa da bandeira: 1132 mm;
- vão da bandeira: 1120x542 mm;
- vidro da bandeira: 1112x534 mm.

Custo de vedações:

**R$ 36,954800**

Custo técnico atual:

**R$ 1.978,438530**

## Golden ORCS 11251 — abertura externa

Geometria:

- marco: 1100x2700 mm;
- folha: 1036x2085 mm;
- vidro principal: 856x1905 mm;
- travessa da bandeira: 1032 mm;
- vão da bandeira: 1020x542 mm;
- vidro da bandeira: 1012x534 mm.

Custo de vedações:

**R$ 35,594800**

Custo técnico atual:

**R$ 1.896,606170**

## API

A Fase 15 expõe:

`top_flag_height_mm`

Sem valor ou com zero, o comportamento da v0.14 é preservado.

O endpoint de opções informa explicitamente as restrições do recorte e mantém as demais bandeiras bloqueadas.

## Compra/corte

Permanece bloqueado para GR.

A Fase 15 homologa BOM/custo técnico da bandeira superior simples, mas não promove a família GR ao plano unificado de compra/corte.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–14;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre a main homologada.
