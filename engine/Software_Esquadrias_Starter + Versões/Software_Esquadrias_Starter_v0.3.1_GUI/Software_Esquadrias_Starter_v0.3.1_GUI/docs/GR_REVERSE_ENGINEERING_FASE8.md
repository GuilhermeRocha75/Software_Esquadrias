# GR — Reverse engineering Fase 8

Status: **GR_ENGINE_0.8.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 8 adiciona **janela GR Design 60x78 com vidro inteiro**, mantendo todo o escopo físico da Fase 7.

Recorte liberado nesta fase:

- aplicação: `JANELA`;
- folha: `FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN`;
- quantidade de folhas: 1;
- preenchimento: `VIDRO INTEIRO`;
- módulo: único;
- fechamento: `MAÇANETA COM CREMONA SEM CHAVE`;
- cremona: `CREMONA 2 PONTOS COMP. 800mm E:15mm`;
- dobradiça: `DOBRADIÇA 90MM`;
- sem tela, persiana, bandeiras, travessas ou reforço estrutural opcional.

O conjunto **DOBRADIÇA SISTEMA OB** permanece fora do escopo da v0.8 porque usa ferragens próprias e a relação exata com a cremona ainda não está fisicamente homologada.

## Fonte oficial

Workbook oficial:

`SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

O arquivo é usado como fonte de engenharia e não é versionado no repositório.

## Evidência histórica ORCS

Foram encontrados **91 registros de janela GR com vidro**.

Depois dos filtros técnicos para remover tela, persiana, bandeiras, travessas, reforço opcional e outras variações, restaram **32 casos limpos**.

Distribuição observada:

- 20 com `DOBRADIÇA SISTEMA OB`;
- 12 com `DOBRADIÇA 90MM`;
- 27 com `MAÇANETA COM CREMONA SEM CHAVE`.

A Fase 8 homologa somente os **12 casos com DOBRADIÇA 90MM**, porque esse conjunto reutiliza o baseline de ferragem já confirmado para janela GR.

## Regra física de vedações

A fabricação confirmou em 2026-09-22 que tanto a porta GR Design 60x104 quanto a janela GR Design 60x78 usam os mesmos dois tipos físicos de borracha:

- **BORRACHA DE VIDRO / LAMBRI**: no perímetro onde entra vidro ou lambri;
- **BORRACHA REDONDA**: no marco por dentro e na folha por fora.

Catálogo usado pela Engine:

- `ACB606` — borracha de vidro/lambri;
- `AC0002` — borracha redonda.

A aba GR do XLSM possui condição incorreta em `GR!76:78` que zera essas vedações. A v0.8 preserva a rastreabilidade do legado, mas calcula o custo físico correto.

## Caso de referência — ORCS 11480

Configuração:

- 700 x 2500 mm;
- 1 folha;
- janela GR Design 60x78;
- vidro `06mm TEMPERADO INCOLOR`;
- dobradiça 90 mm;
- maçaneta com cremona sem chave;
- cremona 800 mm E:15 mm.

Geometria congelada:

- folha final: 636 x 2436 mm;
- vão de baguete: 516 x 2316 mm;
- vidro: 508 x 2308 mm;
- 1 vidro.

Materiais relevantes:

- perfil da folha: `DE6078`;
- baguete do vidro 6 mm: `BA3518`;
- vidro: `6TI`;
- cremona: `CRE12`;
- vedações físicas: `ACB606` + `AC0002`.

Custo físico atual congelado:

**R$ 1.214,705160**

Custo das vedações:

**R$ 29,856000**

O custo histórico salvo no ORCS não é usado como golden de preço atual; o ORCS serve como evidência de configuração/geometria e o custo atual é reconstruído com o catálogo vigente da Engine.

## Caso de referência — ORCS 11558

Configuração:

- 400 x 1500 mm;
- vidro `20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)`;
- mesmo conjunto 90 mm + cremona 800 mm.

Geometria:

- folha final: 336 x 1436 mm;
- vão de baguete: 216 x 1316 mm;
- vidro: 208 x 1308 mm.

Baguete selecionada:

`BA2018`

Custo físico atual congelado:

**R$ 765,115320**

## Regressões preservadas

A v0.8 promove os resultados das fases anteriores sem alterar sua lógica física:

- porta GR 1 folha com painel;
- porta GR 2 folhas com painel;
- porta GR 1 folha com vidro;
- porta GR 2 folhas com vidro;
- abertura interna e externa;
- monoponto e multiponto;
- janela GR 1 folha com painel.

Golden de regressão da porta 2 folhas + vidro 6 mm:

**R$ 2.071,844850**

## Compra/corte

O plano de compras/corte GR continua **bloqueado** nesta fase.

Motivos:

- modelagem física de estoque e barras ainda precisa ser concluída para GR;
- `DE20150` continua exigindo semântica própria de compra quando há lambri/painel;
- não será exposto comercialmente um plano de compra antes da validação dessas regras.

## Gate da Fase 8

Para considerar `GR_ENGINE_0.8.0` tecnicamente aprovada, o SHA final deve passar:

- suíte completa da Engine;
- suíte completa da API;
- build de produção do Web;
- regressão sem alteração interna de CR e Maxim-Ar;
- comparação da branch contra a `main` homologada.

Não fazer merge em `main` antes desse gate.
