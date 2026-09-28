# GR — Reverse engineering Fase 20

Status: **GR_ENGINE_0.20.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 20 acrescenta o primeiro caso de subdivisão da bandeira inferior:

- porta GR Design 60x104;
- abertura externa;
- 1 folha;
- VIDRO INTEIRO;
- bandeira inferior;
- 2 divisões verticais internas (`AH=2`);
- fechadura monoponto;
- dobradiça Sistema OB;
- sem tela, persiana, travessas na folha ou reforço estrutural opcional.

## Evidência ORCS

### ORCS 10024

- 1980x2150 mm;
- porta externa de 1 folha;
- bandeira inferior de 850 mm;
- AH=2, AI=AJ=AK=0;
- vidro 6 mm temperado incolor;
- monoponto;
- dobradiça Sistema OB;
- AO histórico R$ 3.625,96.

O AO histórico é apenas evidência da configuração. O golden usa catálogo atual e as correções físicas já homologadas.

Casos ainda bloqueados:

- ORCS 14179: AH=3, janela de 2 folhas;
- ORCS 16527: AH=1, janela de 2 folhas com tela.

## Geometria da bandeira

GR!D25:

`((W - 2*40) - AH*36) / (AH+1)`

Para W=1980 e AH=2:

`(1980 - 80 - 72) / 3 = 609,333333 mm`

Altura física recuperada pela topologia Design:

`850 - 58 = 792 mm`

Cada divisor vertical usa GR!D22:

`792 + 12 = 804 mm`

Logo, a bandeira tem:

- 3 vãos de 609,333333x792 mm;
- 2 travessas DE6072 de 804 mm;
- 2 reforços RAG - DE6072 de 804 mm;
- 3 vidros de 601,333333x784 mm.

## Baguetes, vidros e vedações

O perímetro físico completo exige:

- 6 baguetes horizontais de 609,333333 mm;
- 6 baguetes verticais de 792 mm;
- 3 vidros;
- ACB606 no perímetro dos 3 vãos: 8.408 mm.

`GR!G25/G26` não representa esse perímetro completo.

Classificação: **LEGACY_BUG_CONFIRMED_BY_GEOMETRY**.

## Reforço e parafusos

Cada divisor interno recebe RAG - DE6072 e:

`ceil(804 / 400) = 3 PAR2`

Para 2 divisores: 6 PAR2 adicionais.

Total do golden: **55,888 PAR2**.

`GR!G118` omite as travessas verticais internas.

Classificação: **LEGACY_BUG_CONFIRMED_BY_PHYSICAL_RULE**.

## Ferragem OB na porta

ORCS 10024 registra `DOBRADIÇA SISTEMA OB`. As fórmulas GR!105:110 são acionadas por U3 e não restringem a aplicação a janela. A Fase 20 inclui uma unidade de cada componente DOB6:DOB11.

GR!G119 para U3=1, P3=1 e uma folha:

`(1*8) + (1+1+4)*2 = 20 PAR1`

## Custo técnico atual

- vedações: **R$ 45,906000**;
- total: **R$ 2.010,312591**.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–19;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre a base aprovada da Fase 19.

Compra/corte continua bloqueado para GR.

## Validação candidata

- Engine: 290 testes verdes;
- API: 61 testes verdes;
- Web: build Vite verde.
