# GR — Reverse engineering Fase 13

Status: **GR_ENGINE_0.13.0 — APROVADO NO ESCOPO DA FASE 13**

## Escopo novo

A Fase 13 completa o último modo de persiana realmente encontrado no histórico GR:

`MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES`

Recorte inicial homologável:

- aplicação: PORTA;
- 2 folhas;
- Design 60x104, abertura interna ou externa;
- VIDRO INTEIRO;
- caixa de 200 mm;
- tala PVC 40 mm;
- dois painéis de persiana;
- dois eixos independentes.

## Evidência histórica

Existem **6 registros GR** com este modo.

Caso de referência:

### ORCS 4109

- porta 2550x2260;
- 2 folhas;
- abertura interna;
- vidro 6 mm temperado incolor;
- monoponto;
- dobradiça 90 mm;
- persiana manual em 2 painéis com eixos independentes.

Os demais casos históricos incluem combinações ainda fora do recorte atual, principalmente janelas/telas, e não são usados como golden desta fase.

## Geometria

Para 2 painéis independentes:

- caixa = `W - 15`;
- guias laterais = `H - 200`, quantidade 2;
- guia central `327204` = `H - 200`, quantidade 1;
- largura por tala = `((W - 2*32 - 30) / 2) - 10`;
- quantidade física de talas = `ceil(H/40) * 2`;
- terminal = largura da tala, quantidade 2;
- eixo = `W/2 - 40`;
- quantidade física de eixos = **2**.

## Correção física dos eixos

O XLSM calcula corretamente o comprimento de meia largura para o eixo, mas registra apenas **1 peça**.

A CR já homologada contém a mesma inconsistência e sua Engine corrige para dois eixos físicos.

A Fase 13 aplica a mesma correção:

- `375021` — 2 eixos;
- um por painel.

Classificação:

**LEGACY_BUG_CONFIRMED_BY_SHARED_ENGINEERING_RULE**

## Divisor de eixos independentes

O XLSM contém em uma condição o texto:

`INDEPENDNETES`

em vez de:

`INDEPENDENTES`

Esse erro pode fazer o modelo selecionar indevidamente o divisor de eixo único.

A regra física já homologada na CR é:

- `371127` — divisor de eixos independentes: 1 unidade;
- `371143` — divisor de eixo compartilhado: 0 unidades.

A v0.13 preserva apenas o divisor correto.

Classificação:

**LEGACY_BUG_CONFIRMED**

## Kit manual de 2 painéis

A Fase 13 usa:

- 2x `370113` — tampas laterais;
- 2x `371513_4` — placas de polia;
- 1x `371127` — divisor independente;
- 2x `375110` — polias;
- 2x `375213` — ponteiras;
- 2x `375234` — adaptadores;
- 2x `375339` — recolhedores;
- 1x `373128` — convite para guias;
- 4x `375678` — engates primeira tala;
- 2x `375415` — passadores frontais;
- 4x `375441` — limitadores.

Como nas Fases 11–12, as auxiliares quebradas da GR são recuperadas pela estrutura equivalente já homologada na CR.

## Golden ORCS 4109

Geometria física:

- vão principal = 2060 mm;
- folha = 1233x2023 mm;
- vidro = 1053x1843 mm;
- caixa = 2535 mm;
- guias laterais = 2060 mm;
- guia central = 2060 mm;
- tala = 1218 mm;
- quantidade de talas = 114;
- eixo = 1235 mm;
- quantidade de eixos = 2.

Custo de vedações:

**R$ 62,643200**

Custo persiana:

**R$ 1.783,634250**

Custo técnico atual:

**R$ 4.503,650750**

O custo AO histórico permanece apenas como evidência de configuração porque o legado não inclui corretamente todo o kit físico.

## Cobertura de persiana após Fase 13

Com a v0.13 ficam cobertos **todos os modos de persiana realmente presentes no ORCS GR**:

- manual em painel único;
- automatizada com botoeira em painel único;
- automatizada com controle remoto em painel único;
- manual em 2 painéis com eixos independentes.

Modos sem histórico GR continuam bloqueados por ausência de evidência.

## Próximo bloco

Após aprovação da Fase 13, a próxima expansão GR é **TELA**, que aparece em cerca de 20 registros históricos e possui lógica separada na aba GR.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–12;
- CR/Maxim-Ar sem alteração interna;
- branch linear sobre main.
