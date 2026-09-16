# GR — Reverse engineering Fases 2 e 3

Status: **GR_ENGINE_0.3.0 — CANDIDATO À AUDITORIA**

## Fonte oficial

Workbook: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

A análise permanece read-only sobre a estrutura OOXML do XLSM oficial. A aba técnica `GR` contém as fórmulas usadas como oráculo; `ORCS` fornece snapshots reais para paridade.

## Evolução da Fase 2 — fechamento multiponto

A Fase 2 mantém o mesmo recorte físico da v0.1 e adiciona:

- fechamento `MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE`;
- `FEC5 — FECHADURA MULTIPONTO (GIRO)`, 1 un, R$ 100,00;
- `CON1 — CONTRA FECHO STANDARD`, 4 un, R$ 5,40/un;
- `CON2 — CONTRA-TESTA`, 1 un;
- `CIL1 — CILINDRO 45X45MM`, 1 un;
- parafusos de ferragem passam de 28 para 36 un.

O delta multiponto versus monoponto é completamente explicado pelas fórmulas do XLSM:

- FEC5 − FEC6: **R$ 45,00**;
- 4 × CON1: **R$ 21,60**;
- 8 parafusos PAR1 adicionais: **R$ 1,20**;
- delta total: **R$ 67,80**.

Paridade atual comprovada:

| ORCS | Medida | Fechamento | Total XLSM/Engine |
|---:|---:|---|---:|
| 18237 | 800×2100 | multiponto | 1401,8744382857144 |
| 18361 | 900×2100 | multiponto | 1452,5236454285714 |
| 18590 | 900×2100 | multiponto | 1452,5236454285714 |
| 18695 | 900×2150 | multiponto | 1472,9345311428572 |
| 18700 | 750×2150 | multiponto | 1395,8748275714288 |

Golden congelado da Fase 2: `test_cases/gr_golden_v0_2.json`.

## Evolução da Fase 3 — abertura externa Design 60×104

A Fase 3 adiciona o segundo sistema de folha comprovado:

- `FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN` → perfil `DE60104`, R$ 55,40/m;
- `FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN` → perfil `DE60104-E`, R$ 54,87/m.

A geometria da folha permanece igual no recorte homologado; o XLSM muda o perfil/custo conforme `GR!H2` e `LISTAPERFIS!A20/A21`.

### Caso real principal da abertura externa

Registros `ORCS` 18545, 18547 e 18558:

- largura: 800 mm;
- altura: 2150 mm;
- 1 folha;
- porta;
- abertura externa Design 60×104;
- painel completo;
- multiponto;
- guarnição 70 mm;
- barra chata 30 mm;
- dobradiça 90 mm;
- total gravado: **R$ 1.418,5308554285714**.

A Engine reproduz **R$ 1.418,530855** após arredondamento a 6 casas.

Geometria desse cenário:

- marco final/corte: 800/805 × 2150/2153 mm;
- folha final/corte: 736/741 × 2113/2118 mm;
- baguete/painel: 564 × 1941 mm;
- faixas de painel: 13,121429;
- reforço marco: 684 × 2034 mm;
- reforço folha: 616 × 1993 mm.

Comparando o mesmo cenário com abertura interna, o custo é R$ 1.421,561395. O delta de **R$ 3,030540** é exatamente o efeito da diferença de R$ 0,53/m nos 5,718 m de perfil de folha calculados.

Golden congelado da Fase 3: `test_cases/gr_golden_v0_3.json`.

## Escopo atual do GR_ENGINE_0.3.0

Suportado:

- porta;
- 1 folha;
- Design 60×104;
- abertura interna ou externa;
- painel completo;
- módulo único;
- fechamento monoponto ou multiponto com chave;
- dobradiça 90 mm;
- guarnição interna 70 mm;
- barra chata externa 30 mm;
- sem persiana;
- sem tela;
- sem bandeiras;
- sem travessas;
- sem reforço estrutural opcional.

Tudo fora do recorte continua bloqueado explicitamente.

## Plano de compra / corte

Ainda não liberado para GR.

Motivo: a fórmula `GR!G41` representa `DE20150` com quantidade fracionária de faixas derivada de altura/140. Antes de integrar GR ao FFD compartilhado, é necessário modelar como essa quantidade se converte fisicamente em barras/peças compráveis e cortáveis. Não será feita aproximação por analogia.

## Questão física pendente — AC0312

`GR!G83` cobra **4 unidades de `AC0312 — CALÇO DE VIDRO 3X12` mesmo no cenário PAINEL COMPLETO sem vidro**.

A Engine mantém a linha `LEGACY_PANEL_BLOCK` exclusivamente para preservar paridade com o XLSM até resposta da fabricação.

Classificação: `PHYSICAL_EVIDENCE_REQUIRED`.

Essa dúvida não bloqueia as Fases 2/3 porque a regra é preservada exatamente como no legado. Ela deverá ser resolvida antes da homologação final da família GR ou antes de liberar uma lógica física de produção/painel.

## Gate

CR `0.5.0` e Maxim-Ar `0.3.0` permanecem congelados. A branch GR não deve ser mesclada em `main` enquanto o escopo total previsto para a fase de homologação GR não estiver fechado e auditado independentemente.
