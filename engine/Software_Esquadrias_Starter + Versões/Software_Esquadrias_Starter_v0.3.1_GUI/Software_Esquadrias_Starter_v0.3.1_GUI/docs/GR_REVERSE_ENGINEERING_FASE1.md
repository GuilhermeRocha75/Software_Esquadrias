# GR — Reverse engineering Fase 1

Status: **GR_ENGINE_0.1.0 — CANDIDATO À AUDITORIA**

## Fonte oficial

Workbook: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256 confirmado:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

A fonte oficial não é versionada no Git. A leitura desta fase foi feita de forma read-only a partir da estrutura OOXML do XLSM.

## Identificação da família

No legado, `GR` representa esquadrias **de giro**. A aba técnica calculável é `GR`; `GR_INT` existe, porém não contém fórmulas de cálculo no workbook oficial analisado.

Estrutura observada:

- `GR`: 736 fórmulas ativas, dimensão aproximada `A1:AU122`.
- `GR_INT`: 0 fórmulas ativas.
- `ORCS`: histórico de entradas/resultados, sem fórmulas.
- Registros `ORCS` com família `GR`: **1.684**.

Distribuição principal encontrada em `ORCS`:

- aplicação: 1.537 portas, 146 janelas e 1 registro legado atípico;
- folhas: 1.484 com 1 folha e 200 com 2 folhas;
- folha porta abertura interna Design 60x104: 1.196;
- folha porta abertura externa Design 60x104: 349;
- folha janela abertura externa Design 60x78: 138;
- painel completo: 1.100;
- sem tela: 1.664;
- sem persiana: 1.617;
- módulo único: 1.683.

## Escopo do GR_ENGINE_0.1.0

Esta primeira versão deliberadamente cobre apenas o recorte com evidência mais forte e alta recorrência:

- aplicação `PORTA`;
- 1 folha;
- `FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN`;
- `PAINEL COMPLETO`;
- `MÓDULO ÚNICO`;
- sem persiana;
- sem tela mosquiteira;
- sem bandeiras;
- sem travessas na folha;
- sem reforço estrutural opcional;
- fechamento `MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE`;
- dobradiça `DOBRADIÇA 90MM`;
- acabamento interno `GUARNIÇÃO DE 70MM`;
- acabamento externo `BARRA CHATA DE 30MM`.

Há **580 registros ORCS** que coincidem com esse baseline funcional.

Tudo fora desse recorte é recusado explicitamente pela Engine v0.1.0, em vez de ser calculado por analogia.

## Fórmulas principais comprovadas

Os números abaixo se referem às fórmulas atuais da aba `GR` e aos valores de catálogo do workbook oficial.

### Marco e folha

Parâmetros relevantes de `PFAB`:

- `B1 = 5` mm — solda 45/45;
- `B2 = 3` mm — solda 45/90;
- `B6 = 8` mm — sobreposição giro Design;
- `B8 = 5` mm — folga inferior giro;
- `B14 = 140` mm — acréscimo acabamento interno;
- `B15 = 60` mm — acréscimo acabamento externo.

Para largura `W` e altura `H` do baseline:

- `GR!D8 = W` — largura final do marco;
- `GR!E8 = W + 5` — corte horizontal do marco;
- `GR!D9 = H` — altura final do marco, sem persiana/bandeiras neste recorte;
- `GR!E9 = H + 3` — corte vertical do marco;
- `GR!D10 = W - 64` — largura final da folha;
- `GR!E10 = W - 59` — corte horizontal da folha;
- `GR!D11 = H - 37` — altura final da folha;
- `GR!E11 = H - 32` — corte vertical da folha.

Perfis principais do baseline:

- `DE6058` — marco alto de abrir, R$ 38,45/m;
- `DE60104` — folha porta de giro abertura interna 60x104, R$ 55,40/m.

### Painel completo

`LISTAPERFIS!E20 = 86` mm para a folha 60x104.

- baguete horizontal: `GR!D16 = D10 - 2*86 = W - 236`;
- baguete vertical: `GR!D17 = D11 - 2*86 = H - 209`;
- `GR!D18 = -104` no baseline, mas `GR!G18 = 0`, portanto a linha não entra como peça;
- quantidade fracionária de painel `DE20150`: `GR!G41 = (D17 + D18)/140`;
- comprimento de cada faixa do painel: `GR!D41 = D16`.

A quantidade fracionária de `DE20150` é uma regra explícita do legado e é preservada nesta fase.

### Acabamentos

- guarnição interna horizontal: `W + 140`, quantidade 1;
- guarnição interna vertical: `H + 140`, quantidade 2;
- barra chata externa horizontal: `W + 60`, quantidade 1;
- barra chata externa vertical: `H + 60`, quantidade 2.

### Reforços ordinários

- marco horizontal: `W - 116`, quantidade 1;
- marco vertical: `H - 116`, quantidade 2;
- folha horizontal: `(W - 64) - 120 = W - 184`, quantidade 2;
- folha vertical: `(H - 37) - 120 = H - 157`, quantidade 2.

Materiais:

- `RAG - DE6058`, R$ 8,00/m;
- `RAG - DE60104`, R$ 25,00/m.

### Ferragens e acessórios do baseline

- `DOB3` — dobradiça 90 mm: 3 un;
- `MAC4` — maçaneta dupla: 1 un;
- `FEC6` — fechadura monoponto: 1 un;
- `CIL1` — cilindro 45x45: 1 un;
- `CON2` — contra-testa: 1 un;
- `AC0001` — tapa deságue: 1 un;
- `PAR1` — parafusos de ferragem: 28 un;
- `PAR2` — parafusos de reforço: 4 por metro conforme o somatório legado das peças reforçadas.

## Paridade XLSM × ORCS × Engine

A reconstrução foi validada primeiro contra as fórmulas da aba `GR` e depois contra snapshots reais gravados em `ORCS` que usam o mesmo baseline e preços compatíveis com o catálogo atual.

| ORCS | Medida | Total calculado pelas fórmulas atuais | Total salvo em ORCS | Delta relevante |
|---:|---:|---:|---:|---:|
| 17386 | 700×2100 | 1283,4252311428572 | 1283,4252311428572 | 0 |
| 17173 | 800×2100 | 1334,0744382857145 | 1334,0744382857142 | ruído de ponto flutuante |
| 18542 | 900×2100 | 1384,7236454285714 | 1384,72 | 0,003645 por armazenamento em centavos |
| 17374 | 1100×2100 | 1486,0220597142861 | 1486,022059714286 | ruído de ponto flutuante |

O golden v0.1 usa 900×2100 como cenário principal e congela geometria, BOM e custo técnico. Outros três casos de largura formam paridade complementar.

Valores históricos mais antigos podem divergir por preço de catálogo alterado ao longo do tempo; eles não devem ser usados como expectativa de custo corrente sem normalização de preços.

## Golden principal — 900×2100

Geometria comprovada:

- marco final/corte: 900/905 × 2100/2103 mm;
- folha final/corte: 836/841 × 2063/2068 mm;
- baguete/painel: 664 × 1891 mm;
- quantidade de faixas do painel: 12,764286;
- reforço marco: 784 × 1984 mm;
- reforço folha: 716 × 1943 mm.

Custo técnico atual:

`R$ 1.384,723645`

O arquivo congelado é `test_cases/gr_golden_v0_1.json`.

## Ponto de atenção físico

`GR!G83` cobra **4 unidades de `AC0312 — CALÇO DE VIDRO 3X12` mesmo em PAINEL COMPLETO sem vidro**.

Nesta fase a Engine mantém essa linha exclusivamente para obter paridade com o XLSM e a identifica como `LEGACY_PANEL_BLOCK`. Não há evidência suficiente ainda para classificar a regra como correta ou como bug físico.

Classificação atual: `PHYSICAL_EVIDENCE_REQUIRED`.

Antes de uma futura homologação completa da família GR, a fabricação deve confirmar se esses quatro calços têm função física no painel ou se são resíduo de regra de vidro.

## Fora do escopo da v0.1

Permanece para fases posteriores:

- porta abertura externa;
- janela abertura externa 60x78;
- 2 folhas;
- folhas com vidro;
- composição superior vidro/inferior painel;
- fechadura multiponto;
- maçaneta com cremona;
- dobradiça sistema OB / pêrnio;
- tela mosquiteira;
- persianas;
- bandeiras superior/inferior;
- travessas AF/AG;
- reforço estrutural opcional;
- cotas personalizadas e demais combinações raras do histórico.

Esses ramos não devem ser liberados por analogia. Cada um precisa de nova leitura das fórmulas e paridade própria.

## Política de homologação

`GR_ENGINE_0.1.0` é somente **candidato à auditoria**.

CR e Maxim-Ar permanecem congelados. Nenhuma regra de `CR_ENGINE_0.5.0` ou `MX_ENGINE_0.3.0` foi alterada para implementar este baseline.

Não fazer merge da branch GR em `main` enquanto o CI e a auditoria independente desta fase não estiverem concluídos.
