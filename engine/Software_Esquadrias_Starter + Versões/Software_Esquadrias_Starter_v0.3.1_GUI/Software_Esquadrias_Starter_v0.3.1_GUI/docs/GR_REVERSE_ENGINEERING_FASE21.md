# GR — Reverse engineering Fase 21

Status: **GR_ENGINE_0.21.0 — APROVADO NO ESCOPO DA FASE 21**

## Escopo novo

A Fase 21 acrescenta o caso ORCS 14179:

- janela GR Design 60x78;
- abertura externa;
- 2 folhas;
- VIDRO INTEIRO;
- bandeira inferior de 700 mm;
- 3 divisões verticais internas (`AH=3`);
- maçaneta com cremona;
- dobradiça 90 mm;
- sem tela, persiana, travessas na folha ou reforço estrutural opcional.

## Evidência ORCS 14179

- 4200x1900 mm;
- quantidade 1;
- vidro duplo 20 mm float incolor/temperado incolor (4/10/6);
- AH=3, AI=AJ=AK=0;
- AO histórico R$ 3.418,45.

O AO histórico identifica a configuração. O golden usa catálogo atual e as
correções físicas já homologadas.

Permanece bloqueado:

- ORCS 16527: AH=1, janela de 2 folhas com tela.

## Janela de duas folhas

GR!D10 para duas folhas:

`((4200 - 80 - 36) / 2) + 16 = 2058 mm`

A correção física da bandeira inferior já homologada na Fase 17 produz:

`H_folha = 1900 - 700 - 42 = 1158 mm`

Cada folha possui:

- baguete 1938x1038 mm;
- vidro 1930x1030 mm;
- 3 dobradiças 90 mm;
- 4 calços.

A folha passiva mantém 2 FEC7 e 2 CON3, conforme regra física homologada para
duas folhas na Fase 5.

## Geometria da bandeira

GR!D25:

`((W - 2*40) - AH*36) / (AH+1)`

Para W=4200 e AH=3:

`(4200 - 80 - 108) / 4 = 1003 mm`

Altura física:

`700 - 58 = 642 mm`

Cada divisor vertical usa GR!D22:

`642 + 12 = 654 mm`

Logo, a bandeira tem:

- 4 vãos de 1003x642 mm;
- 3 travessas DE6072 de 654 mm;
- 3 reforços RAG - DE6072 de 654 mm;
- 4 vidros de 995x634 mm.

## Baguetes, vidros e vedações

O perímetro físico completo exige:

- 8 baguetes horizontais de 1003 mm;
- 8 baguetes verticais de 642 mm;
- 4 vidros na bandeira;
- ACB606 no perímetro dos 4 vãos: 13.160 mm.

`GR!G25/G26` retorna somente 6 baguetes por orientação e não representa o
perímetro físico completo.

Classificação: **LEGACY_BUG_CONFIRMED_BY_GEOMETRY**.

## Reforço e parafusos

Cada divisor interno recebe RAG - DE6072 e:

`ceil(654 / 400) = 2 PAR2`

Para 3 divisores: 6 PAR2 adicionais.

Total do golden: **123,024 PAR2**.

`GR!G118` omite as travessas verticais internas.

Classificação: **LEGACY_BUG_CONFIRMED_BY_PHYSICAL_RULE**.

## Custo técnico atual

- vedações: **R$ 86,280000**;
- total: **R$ 4.131,000880**.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–20;
- CR e Maxim-Ar sem alteração interna;
- GitHub Actions verde na branch `feature/gr-engine-v1`;
- `main` intacta.

Compra/corte continua bloqueado para GR.

## Validação candidata

- Engine: 302 testes verdes;
- API: 62 testes verdes;
- Web: build Vite verde.
- commit candidato: `601ad503be8314939589c01371a4650d65819fc9`;
- GitHub Actions: execução 235 verde no commit candidato.
