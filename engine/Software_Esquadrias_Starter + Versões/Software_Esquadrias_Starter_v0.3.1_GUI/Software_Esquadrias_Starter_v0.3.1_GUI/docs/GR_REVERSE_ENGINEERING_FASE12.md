# GR — Reverse engineering Fase 12

Status: **GR_ENGINE_0.12.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 12 amplia a persiana GR para painel único automatizado:

- `AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO`;
- `AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO`.

Permanece todo o escopo da Fase 11:

- caixa 200 mm;
- tala PVC 40 mm;
- preenchimento `VIDRO INTEIRO`;
- porta/janela GR nos recortes já homologados;
- sem tela, bandeiras ou reforço estrutural opcional.

## Evidência histórica

Entre os 67 registros GR com persiana:

- 44 manual em painel único;
- 10 automatizada com controle remoto em painel único;
- 7 automatizada com botoeira em painel único;
- 6 manual em 2 painéis/eixos independentes.

Referências da Fase 12:

- ORCS 11417 — janela 800x1800, remoto, vidro 6 mm;
- ORCS 12395 — janela 300x1200, botoeira, vidro 4 mm.

## Geometria

Os modos automatizados de painel único preservam a mesma geometria validada na Fase 11:

- caixa = `W - 15`;
- guias laterais = `H - 200`;
- tala = `W - 74`;
- quantidade física de talas = `ceil(H / 40)`;
- terminal = mesma largura da tala;
- eixo = `W - 40`;
- altura útil da esquadria abaixo da caixa = `H - 200`.

## Kit lateral automatizado

Para painel único automatizado:

- 1x `370113` — tampa lateral para polia/ponteira;
- 1x `371513_2` — placa de contenção/ponteira;
- 1x `370141` — tampa lateral para motor;
- 1x `371553` — placa lateral para motor;
- 1x `375213` — ponteira;
- 1x `375234` — adaptador 40/60;
- 1x motor;
- 1x `373128` — convite para guias;
- 2x `375678` — engate da primeira tala;
- 2x `375441` — limitador.

Não entram no modo automatizado:

- placa de polia manual;
- polia;
- recolhedor;
- passador frontal.

Essas quantidades são recuperadas da CR homologada, que utiliza os mesmos códigos físicos e a mesma estrutura de persiana.

## Motor controle remoto

Para:

`AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO`

usar:

- `MOT1`;
- MOTOR DE PERSIANA CONTROLE REMOTO;
- R$ 500,00.

O XLSM GR já aponta `GR!B97` para `LISTAFERRA!A48`, coerente com o catálogo.

## Motor botoeira — LEGACY_BUG_CONFIRMED

Para:

`AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO`

o XLSM GR usa em `GR!B98`:

`LISTAFERRA!A48`

Isso seleciona indevidamente o motor de controle remoto `MOT1`.

Na CR homologada, o equivalente usa:

`LISTAFERRA!A49`

e o catálogo oficial confirma:

- A48 = `MOT1` — controle remoto — R$ 500,00;
- A49 = `MOT2` — botoeira — R$ 250,00.

A v0.12 usa `MOT2` no modo botoeira.

Classificação:

**LEGACY_BUG_CONFIRMED**

## Golden ORCS 11417 — remoto

Configuração:

- janela 800x1800;
- 1 folha;
- vidro 6 mm temperado incolor;
- cremona padrão;
- dobradiça 90 mm;
- controle remoto.

Geometria:

- vão principal = 1600 mm;
- folha = 736x1536 mm;
- vidro = 608x1408 mm;
- caixa = 785 mm;
- guias = 1600 mm;
- tala = 726 mm;
- 45 talas;
- eixo = 760 mm.

Custo vedações:

**R$ 21,856000**

Custo persiana:

**R$ 1.073,839250**

Custo técnico atual:

**R$ 2.034,046410**

## Golden ORCS 12395 — botoeira

Configuração:

- janela 300x1200;
- 1 folha;
- vidro 4 mm float incolor;
- cremona padrão;
- dobradiça 90 mm;
- botoeira.

Geometria:

- vão principal = 1000 mm;
- folha = 236x936 mm;
- vidro = 108x808 mm;
- caixa = 285 mm;
- guias = 1000 mm;
- tala = 226 mm;
- 30 talas;
- eixo = 260 mm.

Custo vedações:

**R$ 10,856000**

Custo persiana:

**R$ 574,089250**

Custo técnico atual:

**R$ 1.128,451210**

## Gate técnico

Para aprovar a Fase 12:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–11;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre `main`.

Após isso, o próximo bloco natural é:

**MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES**.
