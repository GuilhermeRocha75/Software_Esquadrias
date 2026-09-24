# GR — Reverse engineering Fase 10

Status: **GR_ENGINE_0.10.0 — APROVADO NO ESCOPO DA FASE 10**

## Objetivo

A Fase 10 investiga o modo de preenchimento:

`SUPERIOR VIDRO/INFERIOR PAINEL`

É a próxima variante GR de maior cobertura histórica ainda fora da Engine.

## Fonte oficial

Workbook:

`SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

## Evidência ORCS

Existem **119 registros GR** com `R = SUPERIOR VIDRO/INFERIOR PAINEL`.

Distribuição:

- 112 com 1 folha;
- 7 com 2 folhas;
- 104 com folha de porta abertura interna Design 60x104;
- 15 com folha de porta abertura externa Design 60x104;
- 102 monoponto;
- 17 multiponto;
- 117 com DOBRADIÇA 90MM;
- 2 com DOBRADIÇA SISTEMA OB;
- 118 sem persiana;
- 119 sem tela.

Há 3 registros estruturalmente explícitos no formato atual, com `Cota I > 0` e `Trav. Hor. FLS = 1`:

- ORCS 270 — 800x2100, 1 folha, Cota I 900 mm, vidro 4 mm float, monoponto;
- ORCS 285 — 900x2100, 1 folha, Cota I 1050 mm, vidro 6 mm temperado, multiponto;
- ORCS 3560 — 1670x2050, 2 folhas, Cota I 510 mm, vidro 6 mm temperado, monoponto.

Os outros 116 registros históricos foram gravados sem a Cota I/travessa necessária para reproduzir a divisão pelas fórmulas atuais. Eles servem como evidência de existência/comercialização da variante, mas não como golden geométrico.

## Geometria do XLSM

Para o modo misto, com uma travessa horizontal na folha:

- `GR!G12 = AF2 * G5`: uma travessa `DE6072` por folha quando `AF2 = 1`;
- largura útil comum ao vidro e ao painel: `D13 = D16`;
- altura do vidro superior: `D14 = K14`;
- altura do painel inferior: `D18 = D15`;
- vidro: `D68 = D13 - 8`, `E68 = D14 - 8`;
- painel `DE20150`: quantidade vertical `D18 / 140`.

Para porta Design 60x104, 1 folha, sem bandeiras:

- folha final largura = `W - 64`;
- folha final altura = `H - 37`;
- largura do vão = `folha_largura - 172`;
- comprimento da travessa `DE6072` = `folha_largura - 160`;
- altura do vidro superior = `folha_altura - CotaI - 122`;
- altura do painel inferior = `CotaI - 122`.

Exemplo ORCS 270, 800x2100, Cota I 900:

- folha = 736x2063 mm;
- vão comum = 564 mm;
- vidro superior, vão de baguete = 564x1041 mm;
- painel inferior, vão de baguete = 564x778 mm;
- vidro final = 556x1033 mm;
- travessa DE6072 = 576 mm.

## Baguetes e preenchimentos

Vidro superior:

- baguete selecionada pela espessura do vidro, igual às Fases 6–9;
- 2 peças horizontais + 2 verticais por folha.

Painel inferior:

- baguete fixa `BA2516`;
- 2 peças horizontais + 2 verticais por folha;
- enchimento `DE20150` calculado pela altura do painel inferior.

Em 2 folhas, a regra física já confirmada anteriormente continua válida:

- cada folha tem seu próprio painel;
- portanto o `DE20150` deve ser calculado por folha, mesmo quando o XLSM legado omite o multiplicador.

## Vedações

A confirmação física das Fases 6–9 aplica-se diretamente:

- borracha de vidro/lambri no perímetro do vidro superior;
- borracha de vidro/lambri no perímetro do painel inferior;
- borracha redonda na folha por fora;
- borracha redonda no marco por dentro.

Logo o caminho `ACB606` deve somar os dois perímetros de preenchimento.

## Calços

Permanece a regra física confirmada:

- 4 calços `AC0312` por folha;
- não duplicar por quantidade de preenchimentos dentro da mesma folha.

## Reforço da travessa — RESOLVED_PHYSICAL

A fabricação confirmou em 2026-09-24:

- a divisão é sempre feita com a travessa horizontal `DE6072`;
- dentro dela é usado o reforço `RAG - DE6072`;
- o reforço é fixado com parafuso `PAR2`;
- regra prática: aproximadamente **1 parafuso a cada 40 cm**.

A Engine adota uma regra determinística equivalente:

`ceil(comprimento_da_travessa_mm / 400)`

por travessa, garantindo espaçamento nominal não superior a aproximadamente 400 mm.

O XLSM não inclui esse reforço em `GR!G118`. Com a confirmação da fabricação, essa omissão passa a ser:

**LEGACY_BUG_CONFIRMED**

A v0.10 corrige a quantidade de `PAR2` sem alterar a fórmula histórica dos demais reforços.

## Cota I — RESOLVED_PHYSICAL

A fabricação confirmou que a medida deve ser **flexível** e tomada:

**da extremidade inferior da folha pronta para cima até a posição desejada da travessa horizontal.**

Não existe uma altura fixa obrigatória.

Na API essa medida é representada por:

`mixed_split_from_bottom_mm`

A Engine valida apenas se a medida gera vidro superior e painel inferior geometricamente positivos; não inventa limites comerciais adicionais.

## Escopo implementado da v0.10

A Fase 10 implementa:

- porta GR Design 60x104;
- abertura interna ou externa;
- 1 ou 2 folhas;
- `SUPERIOR VIDRO/INFERIOR PAINEL`;
- uma travessa horizontal `DE6072` por folha;
- um reforço `RAG - DE6072` por travessa;
- divisão flexível a partir da base da folha pronta;
- fechamento monoponto ou multiponto;
- dobradiça 90 mm;
- vidro superior com baguete selecionada pela espessura;
- painel inferior com `BA2516 + DE20150`;
- painel calculado por folha;
- 4 calços `AC0312` por folha;
- borracha de vidro/lambri nos dois preenchimentos;
- borracha redonda em folha e marco;
- correção dos parafusos do reforço da travessa.

Goldens físicos atuais:

- ORCS 270: 800x2100, Cota I 900, vidro 4 mm, monoponto;
- ORCS 285: 900x2100, Cota I 1050, vidro 6 mm, multiponto;
- ORCS 3560: 1670x2050, 2 folhas, Cota I 510, vidro 6 mm, monoponto.

Os custos históricos AO continuam preservados somente como evidência do legado; o golden da Engine usa catálogo atual e regras físicas corrigidas.

## Gate técnico

Para aprovar a Fase 10:

- suíte completa Engine verde;
- suíte completa API verde;
- Web build verde;
- regressão das Fases 1–9;
- nenhum toque nos módulos internos de cálculo de CR/Maxim-Ar;
- comparação limpa contra a `main`.

O plano de compras/corte GR continua bloqueado até sua fase própria.
