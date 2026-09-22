# GR — Reverse engineering Fase 6

Status: **GR_ENGINE_0.6.0 — CANDIDATO À AUDITORIA**

## Escopo

A Fase 6 faz duas mudanças controladas:

1. corrige fisicamente as vedações de todas as variantes GR já suportadas;
2. libera o primeiro recorte com vidro: porta GR Design 60x104, 1 folha, abertura interna ou externa, módulo único, sem persiana/tela/bandeiras/travessas, fechamento monoponto ou multiponto.

A janela com vidro e a porta de 2 folhas com vidro continuam bloqueadas até evidência própria de ferragens/topologia.

## Fonte oficial

Workbook oficial:

`SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

A análise é somente leitura. O XLSM não é versionado no repositório.

## Evidência ORCS de vidro

Há 553 registros GR com vidro preenchido no ORCS.

No recorte limpo de porta interna Design 60x104, 1 folha, sem persiana/tela/bandeiras/travessas e modelo `PORTA 1 FOLHA DE GIRO`, foram identificados **125 casos candidatos limpos** na auditoria de Fase 6.

Combinações de maior frequência nesse recorte incluem:

- 43 casos: `06mm TEMPERADO INCOLOR` + monoponto;
- 23 casos: `08mm TEMPERADO INCOLOR` + monoponto;
- 11 casos: `06mm TEMPERADO INCOLOR` + multiponto;
- 9 casos: `08mm MINI BOREAL` + monoponto.

Os custos históricos são evidência de estrutura/configuração, não preço corrente automático.

## Geometria do vidro — RESOLVED_EXCEL

Para porta 1 folha, sem travessas e sem painel:

- largura final da folha: `W - 64`;
- altura final da folha: `H - 37`;
- largura do vão de baguete: `largura_folha - 172`;
- altura do vão de baguete: `altura_folha - 172`;
- largura do vidro: `largura_baguete - 8`;
- altura do vidro: `altura_baguete - 8`.

Fonte:

- `GR!D13`;
- `GR!D14`;
- `GR!D68 = D13 - PFAB!B12`;
- `GR!E68 = D14 - PFAB!B12`;
- `PFAB!B12 = 8 mm`.

Exemplo 800x2100:

- folha final: 736x2063 mm;
- vão de baguete: 564x1891 mm;
- vidro: **556x1883 mm**;
- quantidade: 1 painel de vidro.

## Seleção de baguete — RESOLVED_EXCEL

A fórmula `GR!B13` seleciona a baguete pela espessura do vidro:

- 4–6 mm: `BA3518`;
- 8–10 mm: `BA3218`;
- 12–18 mm: `BA2516`;
- 19–21 mm: `BA2018`;
- 22–25 mm: `BA1816`;
- 26–30 mm: `BA1216`;
- 31–33 mm: `BA1016`;
- 34 mm: `BA0716`.

A Engine v0.6 usa exatamente essa seleção para o recorte liberado.

## Calços — RESOLVED_PHYSICAL

Permanece a regra já confirmada pela fabricação:

- 4 calços `AC0312` por folha;
- usados para manter a folha no esquadro com vidro ou sem vidro.

Uma porta de 1 folha com vidro usa 4 calços; uma porta de 2 folhas com painel usa 8.

## Vedações — RESOLVED_PHYSICAL / LEGACY_BUG_CONFIRMED

Confirmação da fabricação em 2026-09-22:

- **borracha de vidro**: aplicada onde entra vidro **ou lambri/painel**;
- **borracha redonda**: aplicada no **marco por dentro** e na **folha por fora**;
- existem portanto três caminhos físicos de vedação;
- a mesma regra vale para porta GR Design 60x104 e janela GR Design 60x78.

A nomenclatura da Engine é funcional/física:

1. `GLASS_OR_LAMBRI_SEAL` — BORRACHA DE VIDRO / LAMBRI;
2. `ROUND_SEAL_LEAF` — BORRACHA REDONDA na folha;
3. `ROUND_SEAL_FRAME` — BORRACHA REDONDA no marco.

### Referência do catálogo atual

As próprias fórmulas da aba GR apontam os materiais:

- linha de vidro → `LISTAPERFIS!A53:C53` → código `ACB606`, preço atual R$ 1,80/m;
- linhas folha/marco → `LISTAPERFIS!A55:C55` → código `AC0002`, preço atual R$ 1,60/m.

Os nomes legados de catálogo (`BORRACHA PRIME 6X6` e `BORRACHA MAXIM-AR`) não são usados como descrição física da nova Engine. Os códigos/preços permanecem rastreáveis ao catálogo, enquanto os papéis são nomeados conforme confirmação da fabricação.

### Bug legado 1 — condição que zera todas as vedações

`GR!76:78` condiciona as três vedações a:

`B10 = LISTAPERFIS!A7`

`LISTAPERFIS!A7` é `PR4263`, mas uma GR real usa `DE60104`, `DE60104-E` ou `DE6078`.

Resultado: o Excel zera todas as borrachas da GR.

Classificação: **LEGACY_BUG_CONFIRMED**.

### Bug legado 2 — lambri/painel sem borracha de vidro

Mesmo se a condição acima fosse verdadeira, `GR!G76` usa o perímetro do vão de vidro (`D13/D14`). Em `PAINEL COMPLETO`, esse ramo não representa o perímetro físico do lambri (`D16/D17`).

A fabricação confirmou que a borracha de vidro também é utilizada onde entra o lambri/painel.

Classificação: **LEGACY_BUG_CONFIRMED**.

## Regra física adotada pela v0.6

Por folha:

- borracha vidro/lambri = `2 × (largura do vão + altura do vão)`;
- borracha redonda na folha = `2 × (largura da folha + altura da folha)`;
- borracha redonda no marco = mesmo perímetro de contato da folha, conforme topologia já representada por `GR!G78=G77`.

Em duas folhas, os três caminhos são multiplicados pela quantidade de folhas.

## Correção dos custos já suportados

A v0.5 permanece preservada como referência histórica de paridade do Excel antigo. A v0.6 passa a ser a referência física.

Com catálogo atual:

- porta interna 900x2100, 1 folha, painel, monoponto:
  - v0.5 legado: R$ 1.384,723645;
  - vedações físicas: R$ 27,751600;
  - **v0.6: R$ 1.412,475245**.

- porta interna 900x2100, painel, multiponto:
  - **v0.6: R$ 1.480,275245**;
  - delta multiponto vs monoponto permanece R$ 67,80.

- porta externa 800x2150, painel, multiponto:
  - **v0.6: R$ 1.445,782455**.

- janela 800x1300, painel completo:
  - vedações: R$ 18,856000;
  - **v0.6: R$ 846,578384**.

- porta 1600x2100, 2 folhas, painel, monoponto:
  - vedações: R$ 53,943200;
  - **v0.6: R$ 2.277,196098**.

## Golden de vidro v0.6

Caso principal:

- porta 800x2100;
- abertura interna Design 60x104;
- 1 folha;
- `VIDRO INTEIRO`;
- `06mm TEMPERADO INCOLOR` / código `6TI` / R$ 125,00/m²;
- fechamento monoponto;
- baguete `BA3518`;
- vidro 556x1883 mm;
- área 1,046948 m²;
- custo do vidro R$ 130,868500;
- vedações R$ 26,751600;
- **custo técnico físico v0.6: R$ 1.358,191950**.

Golden:

`test_cases/gr_golden_v0_6.json`

## Limites mantidos

A Fase 6 ainda não libera:

- janela GR com vidro;
- porta GR de 2 folhas com vidro;
- composição `SUPERIOR VIDRO/INFERIOR PAINEL`;
- tela;
- persiana;
- bandeiras;
- travessas;
- reforço estrutural opcional;
- plano de compra/corte GR.

A janela com vidro foi deliberadamente mantida fora do escopo porque os registros recentes mostram variantes com `DOBRADIÇA SISTEMA OB`/ferragens diferentes do baseline de painel já homologado. Não é correto reutilizar automaticamente a ferragem de painel.

## Gate

CR `CR_ENGINE_0.5.0` e Maxim-Ar `MX_ENGINE_0.3.0` permanecem congelados.

A Fase 6 é candidata à auditoria somente após:

1. testes v0.5 legados preservados;
2. golden v0.6 físico;
3. testes Engine v0.6;
4. testes API;
5. Web build;
6. CI independente no SHA final.
