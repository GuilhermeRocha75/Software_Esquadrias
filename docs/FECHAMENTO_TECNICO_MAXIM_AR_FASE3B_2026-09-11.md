# Fechamento técnico — Maxim-Ar Fase 3B

Data: 2026-09-11  
Branch: `feature/maxim-ar-engine-v3`  
Workbook oficial: SHA-256 `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`

## Resultado

A Engine produtiva passa a `MX_ENGINE_0.3.0`; `CR_ENGINE_0.5.0` foi preservada.
As respostas diretas de fabricação foram registradas anonimamente e substituem
as hipóteses da Fase 3A. Nenhum dado pessoal ou orçamento bruto foi versionado.

- PRIME e DESIGN calculam os três percursos físicos de vedação pela geometria
  real. O BOM registra identificador interno, descrição, metros, R$/m, custo e
  origem. O material é configurável e não é apresentado como código legado.
- AF/AG na folha móvel são rejeitados como fisicamente inválidos.
- Bandeiras integradas implementam `(V,H)` e `(V+1)*(H+1)` vidros. O XLSM e a
  `LISTAPERFIS` comprovam `PR4263` no PRIME e `DE6072` no DESIGN, com reforços
  `RAG - PR4263` e `RAG - DE6072`. `ALUM10238/ALUM15338` não são travessas.
- Módulos separados com travessas internas são rejeitados.
- São gerados quatro calços `AC0312` para cada painel de vidro real.
- Reforço estrutural não é obrigatório em módulo separado; é opcional e somente
  permitido nessa condição. A escolha entre `ALUM10238` e `ALUM15338` é manual;
  o XLSM determina um corte na largura por bandeira e a Engine o leva ao BOM/FFD.

## Compatibilidade deliberada

Os comportamentos do XLSM que criavam AF/AG sem perfil, multiplicavam vidros em
módulos separados ou omitiam calços/vedação foram classificados como
`LEGACY_BUG_CONFIRMED` e não foram reproduzidos. O exemplo nominal de 1 × 1 m
não força 12 m: a Engine usa os três perímetros efetivamente calculados.

## Gate

`BLOQUEADORES RESOLVIDOS: 6/6`

`GATE MAXIM-AR: APROVADO`

`MAXIM-AR 100% TECNICAMENTE HOMOLOGADO: SIM`

O gate depende da regressão integral registrada no commit desta entrega.
