# GR — Reverse engineering Fase 22

Status: **GR_ENGINE_0.22.0 — CANDIDATO À HOMOLOGAÇÃO**

## Escopo novo

A Fase 22 acrescenta o caso ORCS 16527:

- janela GR Design 60x78, abertura externa;
- 2 folhas com VIDRO INTEIRO;
- bandeira inferior de 600 mm;
- 1 divisão vertical interna (`AH=1`);
- tela mosquiteira recolhível TL3;
- maçaneta com cremona e dobradiça 90 mm;
- sem persiana, travessas na folha ou reforço estrutural opcional.

## Evidência ORCS 16527

- 3000x2000 mm;
- quantidade 1;
- vidro 5 mm temperado incolor;
- AH=1, AI=AJ=AK=0;
- AO histórico R$ 3.736,92.

O AO histórico identifica a configuração. O golden usa catálogo atual e as
correções físicas já homologadas.

## Geometria

A base da janela de duas folhas é a mesma homologada na Fase 21:

- folha: 1458x1358 mm;
- vidro de cada folha: 1330x1230 mm.

GR!D25 para a bandeira:

`(3000 - 80 - 36) / 2 = 1442 mm`

Altura do vão:

`600 - 58 = 542 mm`

Divisor vertical:

`542 + 12 = 554 mm`

Logo, a bandeira possui:

- 2 vãos de 1442x542 mm;
- 1 DE6072 e 1 RAG - DE6072 de 554 mm;
- 2 vidros de 1434x534 mm;
- 4 baguetes horizontais e 4 verticais;
- 7.936 mm de ACB606 nos dois perímetros.

## Tela TL3

A Fase 14 homologou a correção da referência vazia de `GR!D73/E73` pela
fórmula compartilhada com MX:

`largura_m × 110 + altura_m × 110 + 110`

Para o marco de 3000x2000 mm:

`3,0 × 110 + 2,0 × 110 + 110 = R$ 660,00`

A tela permanece um único conjunto recolhível, inclusive na janela de duas
folhas.

## Reforço e parafusos

O divisor interno recebe:

`ceil(554 / 400) = 2 PAR2`

Total do golden: **99,024 PAR2**.

## Custo técnico atual

- tela: **R$ 660,000000**;
- vedações: **R$ 68,876800**;
- total: **R$ 3.316,784720**.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–21;
- CR e Maxim-Ar sem alteração interna;
- GitHub Actions verde na branch `feature/gr-engine-v1`;
- `main` intacta.

Compra/corte continua bloqueado para GR.

## Validação candidata

- Engine: 314 testes verdes;
- API: 63 testes verdes;
- Web: build Vite verde;
- GitHub Actions: a preencher após publicar o commit candidato.
