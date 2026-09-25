# GR — Reverse engineering Fase 16

Status: **GR_ENGINE_0.16.0 — APROVADO NO ESCOPO DA FASE 16**

## Escopo novo

A Fase 16 amplia a bandeira superior simples para:

- porta GR Design 60x104;
- abertura interna;
- 2 folhas;
- VIDRO INTEIRO;
- dobradiça 90 mm;
- bandeira superior simples, sem subdivisões;
- sem tela, persiana ou reforço estrutural opcional.

O escopo da Fase 15, de 1 folha interna/externa, permanece preservado.

## Evidência ORCS

Golden principal:

### ORCS 14051

- 1472x2700 mm;
- porta de 2 folhas;
- abertura interna;
- bandeira superior 400 mm;
- vidro 6 mm temperado incolor;
- monoponto;
- dobradiça 90 mm;
- sem tela/persiana;
- sem travessas internas registradas.

Custo histórico AO: R$ 2.383,82 — usado apenas como evidência do legado.

## Geometria

A fórmula de largura da folha de 2 folhas já homologada permanece:

`largura_folha = W/2 - 42`

Para 1472 mm:

**694 mm por folha**

A altura com bandeira superior continua:

`altura_folha = H_total - H_bandeira - 15`

Para 2700 / 400 mm:

**2285 mm**

Vidro principal por folha:

- vão de baguete: 522x2113 mm;
- vidro: **514x2105 mm**;
- quantidade: 2.

Bandeira superior:

- travessa limite DE6072: **W - 68 = 1404 mm**;
- vão fixo: **W - 80 x H_bandeira - 58 = 1392x342 mm**;
- vidro fixo: **1384x334 mm**;
- quantidade: 1 vidro contínuo no recorte sem subdivisão.

## Marco integrado — regra crítica

Em porta módulo único:

- `GR!G8 = 1` → um horizontal DE6058;
- `GR!G10 = 4` → quatro peças horizontais/verticais de folha no conjunto de 2 folhas;
- `GR!G19 = 1` → uma travessa horizontal DE6072 da bandeira.

A Fase 16 preserva explicitamente essa topologia para não repetir a supercontagem detectada e corrigida durante a auditoria da Fase 15.

## Parafusos de reforço

`GR!G118` é reproduzido com as quantidades reais:

- marco: G8 = 1;
- folhas: G10 = 4;
- travessa da bandeira: G19 = 1.

No golden ORCS 14051:

**PAR2 = 70,16 unidades técnicas**

## Regras físicas preservadas

2 folhas continuam usando:

- 4 calços AC0312 por folha → 8;
- painel passivo: 2x FEC7 + 2x CON3 quando aplicável;
- sem PAR1 adicional nos kits passivos;
- borracha de vidro/lambri em cada vidro;
- borracha redonda em cada folha/marco.

A bandeira fixa recebe apenas a vedação de vidro/lambri ACB606 no perímetro fixo.

## Custo físico atual — ORCS 14051

Custo de vedações:

**R$ 63,345600**

Custo técnico atual:

**R$ 2.576,578850**

## Restrições

A Fase 16 ainda não libera:

- porta externa de 2 folhas + bandeira sem caso histórico limpo equivalente;
- bandeira inferior;
- bandeiras superior + inferior simultâneas;
- divisões verticais/horizontais internas na bandeira;
- combinação bandeira + tela;
- combinação bandeira + persiana;
- janela de 2 folhas.

## Compra/corte

Continua bloqueado para GR.

## Gate técnico

Aprovar somente com:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–15;
- CR/Maxim-Ar sem alteração interna;
- branch linear sobre a main homologada.
