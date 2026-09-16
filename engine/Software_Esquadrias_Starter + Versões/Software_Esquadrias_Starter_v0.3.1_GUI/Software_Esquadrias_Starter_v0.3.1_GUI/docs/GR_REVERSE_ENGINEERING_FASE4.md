# GR — Reverse engineering Fase 4

Status: **GR_ENGINE_0.4.0 — CANDIDATO À AUDITORIA**

## Fonte oficial

Workbook: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256 confirmado:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

## Evidência física recebida em 2026-09-16

### Quatro calços AC0312

A fabricação confirmou que **4 unidades de `AC0312 — CALCO DE VIDRO 3X12` são utilizadas mesmo em PAINEL COMPLETO sem vidro**.

Função física informada: os quatro calços mantêm a folha no esquadro e impedem que ela ceda.

Classificação:

`RESOLVED_PHYSICAL`

Consequência para a Engine:

- manter quantidade 4;
- renomear o papel técnico para `SQUARING_BLOCK`;
- não tratar mais essa linha como possível bug legado.

### Janela de giro — cremona

A fabricação informou que em **90% ou mais dos casos** a janela de giro usa maçaneta com cremona, sendo **cremona de aproximadamente 800 mm o padrão**.

No XLSM, a folha Design 60x78 usa eixo `E:15mm` (`GR!Q3`). O item de catálogo correspondente é:

- `CRE12` — `CREMONA 2 PONTOS COMP. 800mm E:15mm`;
- preço atual no workbook: R$ 18,30/un.

Para evitar transformar uma frequência em regra universal, a v0.4 homologa somente um recorte explícito e bloqueia as demais variações.

## Escopo novo do GR_ENGINE_0.4.0

Além de todo o escopo preservado das versões 0.1–0.3, a v0.4 adiciona:

- aplicação `JANELA`;
- 1 folha;
- `FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN`;
- `PAINEL COMPLETO`;
- `MÓDULO ÚNICO`;
- sem vidro;
- sem tela;
- sem persiana;
- sem bandeiras;
- sem travessas na folha;
- sem reforço estrutural opcional;
- `MAÇANETA COM CREMONA SEM CHAVE`;
- `CREMONA 2 PONTOS COMP. 800mm E:15mm` (`CRE12`);
- `DOBRADIÇA 90MM`;
- `GUARNIÇÃO DE 70MM`;
- `BARRA CHATA DE 30MM`.

Não foi liberada dobradiça sistema OB nesta fase.

## Fórmulas da janela 60x78 / painel completo

Para largura `W` e altura `H`:

### Marco

- largura final: `W`;
- corte largura: `W + 5`;
- altura final: `H`;
- corte altura: `H + 5`;
- quantidade: 2 horizontais + 2 verticais.

### Folha `DE6078`

- largura final: `W - 64`;
- corte largura: `W - 59`;
- altura final: `H - 64`;
- corte altura: `H - 59`;
- quantidade: 2 horizontais + 2 verticais.

### Baguete e painel

Para `DE6078`, `LISTAPERFIS!D16 = 60` e `LISTAPERFIS!D18 = 18`:

- baguete/painel largura: `W - 184`;
- baguete/painel altura: `H - 184`;
- componente secundário legado `D18 = -78`;
- quantidade fracionária de `DE20150`: `((H - 184) - 78) / 140`;
- comprimento de cada faixa de painel: `W - 184`.

### Reforços

- marco largura: `W - 80`, quantidade 2;
- marco altura: `H - 80`, quantidade 2;
- folha largura: `W - 184`, quantidade 2;
- folha altura: `H - 184`, quantidade 2;
- folha usa `RAG - DE6078`.

### Ferragens do baseline

- `DOB3` — dobradiça 90 mm: 3 un;
- `MAC1` — maçaneta standard: 1 un;
- `CRE12` — cremona 800 mm E:15: 1 un;
- `CON1` — contra-fecho standard: 2 un;
- `AC0312` — calço/esquadrejamento: 4 un;
- `AC0001` — tapa deságue: 2 un;
- `PAR1`: 32 un;
- `PAR2`: conforme metragem reforçada da fórmula `GR!G118`.

## Golden v0.4

Arquivo:

`test_cases/gr_golden_v0_4.json`

Casos congelados:

1. 800×1300 — referência histórica ORCS 17975;
2. 1120×1850 — referência histórica ORCS 18400.

Os registros ORCS desses casos têm o campo de cremona vazio. Portanto os totais salvos no histórico **não são usados como golden exato de custo** da v0.4.

A v0.4 normaliza o BOM segundo a confirmação física e o catálogo atual, incluindo explicitamente `CRE12`.

Custos técnicos v0.4:

- 800×1300: **R$ 827,722384**;
- 1120×1850: **R$ 1.178,777293**.

## Política de segurança da fase

Continuam bloqueados:

- janela com vidro;
- janela com dobradiça sistema OB;
- janela com outra cremona;
- 2 folhas;
- tela;
- persiana;
- bandeiras;
- travessas;
- reforço estrutural;
- compra/corte GR.

Esses ramos somente devem ser adicionados após nova leitura de fórmulas + evidência histórica/física.

CR `CR_ENGINE_0.5.0` e Maxim-Ar `MX_ENGINE_0.3.0` permanecem congelados.

Não fazer merge em `main` antes da auditoria independente da família GR.
