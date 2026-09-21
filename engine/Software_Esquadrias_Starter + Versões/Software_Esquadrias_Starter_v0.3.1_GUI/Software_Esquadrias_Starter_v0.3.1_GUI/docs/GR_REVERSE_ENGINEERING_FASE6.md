# GR — Reverse engineering Fase 6

Status: **EM ANÁLISE — PHYSICAL_EVIDENCE_REQUIRED (VEDAÇÕES GR)**

## Objetivo

A Fase 6 investiga a primeira expansão GR com vidro, começando pelo recorte mais frequente e tecnicamente limpo:

- porta GR Design 60x104;
- 1 folha;
- abertura interna;
- módulo único;
- sem persiana;
- sem tela;
- sem bandeiras;
- sem travessas;
- vidro inteiro;
- fechamento monoponto ou multiponto.

Nenhum código de cálculo para vidro deve ser liberado na API antes de resolver a vedação física.

## Fonte oficial

Workbook oficial:

`SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

A análise é somente leitura. O XLSM não é versionado no repositório.

## Evidência ORCS

Há 553 registros GR com vidro preenchido no ORCS.

No recorte limpo de porta interna Design 60x104, 1 folha, sem persiana/tela/bandeiras/travessas e modelo `PORTA 1 FOLHA DE GIRO`, foram encontrados **125 casos**.

Combinações mais frequentes:

- 43 casos: `06mm TEMPERADO INCOLOR` + monoponto;
- 23 casos: `08mm TEMPERADO INCOLOR` + monoponto;
- 11 casos: `06mm TEMPERADO INCOLOR` + multiponto;
- 9 casos: `08mm MINI BOREAL` + monoponto.

Os custos históricos são usados como evidência, porém não congelados como preço atual quando o catálogo mudou.

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

A mesma tabela já é usada pela Engine Maxim-Ar Design e coincide com o XLSM atual.

## Catálogo atual de referência

Exemplos:

- `06mm TEMPERADO INCOLOR`: código `6TI`, R$ 125,00/m²;
- `08mm TEMPERADO INCOLOR`: código `8TI`, R$ 145,00/m²;
- `04mm FLOAT INCOLOR`: código `4FI`, R$ 75,00/m²;
- `20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)`: código `20FITI(4/10/6L)`, R$ 250,00/m².

## Calços — RESOLVED_PHYSICAL

Permanece a regra já confirmada pela fabricação:

- 4 calços `AC0312` por folha;
- usados para esquadrejar a folha com ou sem vidro.

Logo, uma porta de 1 folha com vidro continua usando 4 calços.

## BLOQUEIO: vedações GR

A aba GR contém três linhas explícitas:

- `GR!76 — Borracha do vidro`;
- `GR!77 — Borracha da folha`;
- `GR!78 — Borracha do Marco`.

As fórmulas de comprimento representam três caminhos distintos:

1. perímetro do vão de vidro;
2. perímetro da folha;
3. segundo perímetro de contato folha/marco.

Para o exemplo 800x2100, sem travessas:

- vedação de vidro: 4,910 m;
- vedação de folha: 5,598 m;
- vedação de marco/contato: 5,598 m;
- total potencial: 16,106 m.

Entretanto, o XLSM condiciona as três linhas a:

`B10 = LISTAPERFIS!A7`

e `LISTAPERFIS!A7` é `TRAVESSA (USADA COMO FOLHA) / PR4263`, não um perfil GR.

Por isso, em qualquer GR real com `DE60104`, `DE60104-E` ou `DE6078`, as três vedações ficam zeradas.

Além disso, os materiais apontados nessas fórmulas são:

- `ACB606 — BORRACHA PRIME 6X6` para vidro;
- `AC0002 — BORRACHA MAXIM-AR` para folha e marco.

Essas referências não são coerentes com a família GR Design e parecem ter sido copiadas de outra lógica.

Classificação atual:

**POSSIBLE_LEGACY_BUG / PHYSICAL_EVIDENCE_REQUIRED**

## Impacto sobre versões anteriores

Se a fabricação confirmar que portas/janelas GR utilizam vedação física de folha/marco, o problema não afeta apenas o vidro da Fase 6.

Ele também significa que os custos v0.1–v0.5 reproduzem uma omissão do XLSM nas vedações de portas/janelas com painel.

Nesse caso será necessário:

1. classificar a omissão como `LEGACY_BUG_CONFIRMED`;
2. corrigir todas as variantes GR já suportadas;
3. criar novo golden com o custo físico correto;
4. preservar goldens anteriores apenas como evidência histórica/legado, não como custo físico final;
5. rodar novamente regressão Engine + API + Web.

## Custo preliminar sem vedação — NÃO HOMOLOGADO

Usando o catálogo atual e reproduzindo literalmente a omissão do XLSM, uma porta 800x2100, 1 folha, abertura interna, vidro `06mm TEMPERADO INCOLOR`, monoponto, resulta em aproximadamente:

**R$ 1.331,440350**

Este valor não deve ser tratado como golden físico enquanto a regra de vedação estiver aberta.

## Próximo gate

A Fase 6 só avança para código após resposta da fabricação sobre:

- existência dos três caminhos de vedação;
- material/código utilizado em cada caminho;
- regra com painel completo versus vidro;
- diferenças, se houver, entre porta 60x104 e janela 60x78.
