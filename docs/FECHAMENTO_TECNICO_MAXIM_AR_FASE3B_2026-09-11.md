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

## AUDITORIA INDEPENDENTE PÓS-FASE3B

Data da correção: 2026-09-15.

### Divergência geométrica PRIME de 6 mm

A auditoria reproduziu no XLSM oficial o caso PRIME 1000 × 3000, uma folha,
bandeira inferior de 1000 mm, `(03)`, módulo único:

| Medida | XLSM | Engine antes | Engine corrigida |
| --- | ---: | ---: | ---: |
| corte da travessa `D14` | 950 | 950 | 950 |
| abertura/baguete `D16` | 938 | 944 | 938 |
| vidro `D60` | 930 | 936 | 930 |
| altura da abertura `D17` | 218,5 | 218,5 | 218,5 |
| altura do vidro `E60` | 210,5 | 210,5 | 210,5 |
| vidros | 4 | 4 | 4 |

Decisão: alternativa A, `ENGINE_BUG_FIXED`. A Engine estava errada e passou a
reproduzir o desconto fixo de 12 mm de `MX!D16/D18`. Não foi encontrada prova
física suficiente para sustentar a divergência anterior. O corte do perfil
permanece em 950 mm; o desconto atua na abertura, baguete e vidro.

Evidências usadas:

- workbook oficial SHA-256
  `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`;
- `MX!D14`, `D16:D19`, `D60:E61`;
- `LISTAPERFIS`: `PR4263`, face de 28 mm e profundidade de 14 mm; `DE6072`,
  face de 36 mm e profundidade de 18 mm;
- `PFAB!B18=12` e `PFAB!B19=6`;
- três snapshots históricos adicionais com a mesma fórmula `D14-12`;
- 17 registros MX PRIME com bandeira integrada no ORCS e croquis históricos,
  que confirmam a topologia, mas não oferecem cota interna que autorize +6 mm.

### Rigor Excel × Engine restaurado

Os testes voltaram a usar igualdade exata quando não existe correção moderna.
Os casos DESIGN com preço configurado zero permanecem iguais ao custo do Excel.
Nos casos divergentes, o teste registra o custo Excel, cada componente alterado,
o delta exato e o custo moderno. Estão cobertos vedação configurável, correção
PRIME vertical, quatro calços por vidro, reforços e parafusos de módulos
separados e grades físicas que corrigem referências inconsistentes do XLSM.

### Golden `MX_ENGINE_0.3.0`

Foi criado `maxim_ar_golden_v0_3.json`, com 28 cenários e preço de vedação de
R$ 1,80/m. O preço vem de `LISTAPERFIS!C53:C54` apenas como valor configurado
de regressão; o identificador continua interno e não representa código legado
obrigatório.

O golden congela geometria, aberturas, vidros, travessas, BOM, custos por grupo,
warnings, custo técnico, plano de compra, FFD, distribuição de cada corte por
barra e kerf. Inclui PRIME/DESIGN simples, múltiplas folhas, vertical, tela,
bandeiras inferior/superior `(00)` e `(03)`, grade V/H, módulos separados,
reforço estrutural opcional, calços e casos ORCS PRIME anonimizados.

Os valores do Excel foram coletados com o arquivo oficial aberto em modo de
leitura, macros e links desabilitados e `CalculateFullRebuild`. O script em
`tools/collect_mx_audit_excel.ps1` valida o SHA-256 antes da coleta e não emite
campos pessoais do ORCS.

### Regressão pós-auditoria

- Engine: 97 testes aprovados, incluindo toda a suíte CR e Maxim-Ar.
- API: 21 testes aprovados, incluindo serialização exata da bandeira PRIME
  `(03)` e vedação com preço não zero.
- Web: build Vite aprovado, 30 módulos transformados.
- `git diff --check`: aprovado.
- `CR_ENGINE_0.5.0`: preservada sem alteração de código.

Decisão pós-auditoria:

`GATE MAXIM-AR: APROVADO`

`MAXIM-AR 100% TECNICAMENTE HOMOLOGADO: SIM`

`É seguro fazer merge em main: SIM`
