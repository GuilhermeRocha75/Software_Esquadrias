# GR — Fase 25: auditoria de fechamentos e ferragens

Status: **auditoria reproduzível; nenhuma fórmula da Engine alterada**.

## Fonte e método

- fonte oficial: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`;
- SHA-256: `96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`;
- leitura direta do OpenXML por `tools/audit_gr_phase25.py`;
- universo: **1.684** registros `GR` da aba `ORCS`;
- campos lidos para o relatório: somente valores técnicos e números de linha;
- `application` (`ORCS I`) é mantida apenas como dado histórico;
- `leaf_system` (`ORCS H`) conduz a classificação física.

O snapshot reproduzível está em `test_cases/gr_hardware_audit_v0_25.json`. A
auditoria é de compatibilidade de ferragens. Limitações ortogonais já abertas
(bandeiras, vidros e outros recursos) não são indevidamente encerradas quando
uma combinação aparece como `ALREADY_SUPPORTED`.

## Resultado das classificações

| Classificação | Registros |
|---|---:|
| `ALREADY_SUPPORTED` | 1.505 |
| `SUPPORTED_AFTER_APPLICATION_INDEPENDENCE` | 13 |
| `REQUIRES_ENGINE_IMPLEMENTATION` | 57 |
| `REQUIRES_PHYSICAL_CONFIRMATION` | 98 |
| `INVALID_SOURCE_DATA` | 11 |
| **Total** | **1.684** |

As 162 combinações detalhadas no JSON cruzam tipo de folha, número de folhas,
aplicação histórica, fechamento, cremona e dobradiça. Cada combinação também
carrega modo de preenchimento, bandeira, tela e persiana, além das linhas ORCS.
Isso evita esconder diferenças de contexto durante a futura implementação.

Separações gerais:

| Dimensão | Valores e contagens |
|---|---|
| Preenchimento | painel completo 1.100; vidro inteiro 465; misto 119 |
| Bandeira | sem 1.638; inferior 23; superior 21; inferior e superior 2 |
| Tela | sem 1.664; com 20 |
| Persiana | sem 1.617; manual única 44; controle remoto 10; botoeira 7; dois painéis independentes 6 |

## Releitura da pendência de 66 registros

A Fase 23 identificou 66 registros pela incompatibilidade entre o fechamento e
a combinação então esperada de aplicação/tipo de folha. A releitura mostra:

| Situação dos 66 | Registros |
|---|---:|
| Resolvidos automaticamente pela independência da Fase 24 | **0** |
| Exigem implementação na Engine | 37 |
| Exigem confirmação física | 25 |
| Fonte inválida/incompleta | 4 |
| **Total** | **66** |

Os 66 já têm aplicação histórica coerente com o tipo de folha e, portanto, são
disjuntos dos 47 casos de independência encerrados na Fase 24. Alterar somente
a interpretação de `application` não troca o conjunto físico de ferragens.

Os casos que exigem implementação são, principalmente, folha de porta com
fechamento de cremona e folha de janela com fechadura mono/multiponto. O XLSM
contém registros e fórmulas, mas a Engine v0.24 não implementa esses conjuntos
como recortes homologados. Eles não foram classificados como suportados por
semelhança.

## Inventário dos fechamentos especiais

Os **18** registros reproduzem exatamente a contagem da Fase 23:

| Fechamento em ORCS P | Frequência | Linhas ORCS |
|---|---:|---|
| vazio | 6 | 10259, 10397, 10398, 13716, 14975, 14976 |
| MAÇANETA COM CHAVE E CREMONA | 3 | 2534, 14835, 17080 |
| MAÇANETA COM CREMONA | 2 | 3369, 17007 |
| 2 FECHADURA ROLETE (PUXADOR POR CONTA DO CLIENTE) | 1 | 16 |
| FECCHADURA ROLETE | 1 | 16476 |
| FECHADURA + PUXADOR | 1 | 16685 |
| FECHADURA IMAB | 1 | 16691 |
| FECHO 1 PONTO | 1 | 17075 |
| MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE + FECHADURA AUXILIAR | 1 | 16918 |
| MAÇANETA DUPLA COM FECHADURA ROLETE E CHAVE | 1 | 17037 |

Os seis vazios são `INVALID_SOURCE_DATA`. Os demais precisam de confirmação
do conjunto físico completo antes de qualquer implementação. A grafia
`FECCHADURA ROLETE` foi preservada como evidência da fonte, sem normalização
silenciosa.

## Cremonas

Em `ORCS Q`, 1.678 registros estão vazios. Os seis valores preenchidos são:

| Valor técnico | Frequência |
|---|---:|
| CREMONA OSCILO/GIRO COMP. 1100MM E:15MM | 3 |
| CREMONA OSCILO/GIRO COMP. 1400MM E:15MM | 1 |
| VEDA FRESTA NA FOLHA | 1 |
| VEDA FRESTA NAS DUAS FOLHAS. | 1 |

Os dois textos de vedação são contaminação clara da coluna de cremona. Uma
cremona OB gravada junto de fechamento multiponto com dobradiça 90 mm também
foi mantida como fonte inválida. Para dobradiça Sistema OB com fechamento de
cremona e `Q` vazio, o comprimento não foi inferido: é necessária confirmação
física.

## Dobradiça pêrnio e interseções

Os cinco casos pendentes são todos `DOBRADIÇA PÉRNIO`:

| Frequência | Linhas ORCS |
|---:|---|
| 5 | 784, 3190, 3191, 7084, 7536 |

Não existe interseção entre esses cinco casos e os 18 fechamentos especiais.
O catálogo contém `DOB5`, mas presença em catálogo não comprova quantidade,
parafusos, usinagem nem compatibilidade por tipo de folha. Os cinco casos
permanecem em `REQUIRES_PHYSICAL_CONFIRMATION`.

## Dados incompletos ou inválidos

Foram separados 11 registros nas linhas ORCS **158, 543, 914, 10259, 10397,
10398, 13661, 13663, 13716, 14975 e 14976**. Os motivos são fechamento vazio,
tipo de folha/aplicação inválida ou valor incompatível na coluna de cremona.
Nenhum valor foi completado por inferência.

## Fórmulas GR 105 a 119

O script congela as fórmulas OpenXML e as referências de catálogo. O resumo
técnico é:

| GR | Ativação/quantidade | Material ou referência |
|---:|---|---|
| 105 | OB: 1 por folha; não OB: 3 por folha | OB `DOB6`; caso contrário seleção `U2` |
| 106 | somente OB, 1 por folha | `DOB7` |
| 107 | somente OB, 1 por folha | `DOB8` |
| 108 | somente OB, 1 por folha | `DOB9` |
| 109 | somente OB, 1 por folha | `DOB10` |
| 110 | somente OB, 1 por folha | `DOB11` |
| 111 | sempre 1 | P3 1/2: `MAC4`; P3 3: `MAC1`; demais: `MAC5` |
| 112 | sempre 1 | P3 1: `FEC5`; P3 2: `FEC6`; demais: `Q2` |
| 113 | P3 1/2, quantidade 1 | `CIL1` |
| 114 | P3 1: 4; P3 2: 0; demais: 2 | `CON1` |
| 115 | P3 1/2, quantidade 1 | `CON2` |
| 116 | duas folhas, quantidade 2 | `CON3` |
| 117 | duas folhas, quantidade 2 | `FEC7` |
| 118 | comprimentos/quantidades dos perfis reforçados | `PAR2` |
| 119 | `(G105*8)+(G111+G112+G114)*2` | `PAR1` |

As referências OB são `LISTAFERRA!A61:C66`; os componentes de fechamento usam
as linhas 24, 35, 50 a 55, 72 e 73; `PAR1` e `PAR2` usam as linhas 46 e 47.

A regra legada de `PAR1` conta oito parafusos por unidade de `G105` e dois por
unidade de `G111`, `G112` e `G114`. Ela não soma `G106:G110`, `G113` ou
`G115:G117`. Esta auditoria registra o fato; não corrige nem altera a fórmula.

## Confirmações físicas ainda necessárias

Antes da implementação devem ser confirmados:

1. conjunto completo, quantidades, usinagem e parafusos da dobradiça pêrnio;
2. material exato e quantidade de cada fechamento especial;
3. comprimento da cremona nos registros Sistema OB com `ORCS Q` vazio;
4. validade física de Sistema OB com duas folhas;
5. validade dos conjuntos OB em folha interna e em folha de janela com
   fechadura mono/multiponto;
6. intenção dos registros incompletos, sem preencher dados por aproximação.

## Gate

Esta etapa não cria `GR_ENGINE_0.25.0`, não altera cálculos e não fecha o gate
de cobertura histórica. CR e Maxim-Ar permanecem inalterados.
