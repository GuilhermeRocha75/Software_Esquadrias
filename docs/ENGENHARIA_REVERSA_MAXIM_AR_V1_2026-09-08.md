# Engenharia reversa — Maxim-Ar V1

Data da extração: 2026-09-09  
Arquivo solicitado para o marco: `ENGENHARIA_REVERSA_MAXIM_AR_V1_2026-09-08.md`

## Fonte e rastreabilidade

- Pasta de trabalho: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`.
- SHA-256: `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`.
- Aba técnica encontrada: `MX`, intervalo usado `A1:AU85`, com 715 células e 491 fórmulas armazenadas.
- Tabelas consultadas: `LISTAPERFIS`, `LISTAFERRA`, `LISTAVIDROS`, `PFAB` e `ORCS`.
- A aba `ORCS` possui 18.721 linhas de dados. Foram identificados 3.636 registros com família `MX` e descrição contendo `MAXIM-AR`.
- O XLSM não foi copiado para o Git: contém nomes e histórico de clientes. A prova reproduzível é o hash acima, as referências de células e o golden anonimizado.

O Excel foi aberto em modo somente leitura, com macros desabilitadas, e recalculado pelo Excel 16.0. Nenhuma célula do arquivo original foi salva.

## Inventário dos campos

| Coluna MX/ORCS | Rótulo legado | Interpretação encontrada |
| --- | --- | --- |
| A–F | cliente, nome, item, largura, altura, quantidade | Identificação comercial e dimensões externas em mm |
| G | Nº folhas | De 1 a 8 folhas nos dados; Fase 1 cobre 1 folha |
| H | Tipo de folha | `42X63MM - PRIME` ou `60X78MM - DESIGN` |
| I | Aplicação | Na MX significa orientação `HORIZONTAL`/`VERTICAL`, não aplicação janela/porta |
| J | Local | Campo comercial, sem efeito técnico na MX |
| K | Vidros | Chave exata de `LISTAVIDROS` |
| L–N | Persiana, caixa, talas | Presentes no contrato comum; não participam das fórmulas-base MX examinadas |
| O | Tela mosquiteira | Aciona a tela recolhível da linha 64 |
| P–Q | fechamento, cremona | Fecho de 1 ponto ou maçaneta com cremona Maxim-Ar |
| R | Roldanas | Na MX armazena a opção de reforço estrutural; rótulo herdado é enganoso |
| S–T | acabamentos | Interno e externo |
| U | Dobradiça | Na MX armazena `MÓDULO ÚNICO`/`MÓDULOS SEPARADOS`; rótulo herdado é enganoso |
| V–AE | Cotas A–K | Cotas auxiliares para travessas e bandeiras |
| AF–AK | travessas | Quantidades H/V na folha e nas bandeiras inferior/superior |
| AL | margem | Comercial; não pertence à Engine técnica |
| AM–AU | código/modelos/custo e auxiliares | Campos calculados e descrições derivadas |

## Frequência observada na ORCS

- Folhas: 3.129 de uma folha; 373 de duas; 91 de três; 33 de quatro; demais 10.
- Sistemas: 2.413 DESIGN; 1.221 PRIME; duas grafias inválidas isoladas.
- Orientação: 3.583 horizontal; 53 vertical.
- Tela: 3.044 sem tela; 592 com tela.
- Fechamento: 3.626 fecho de 1 ponto; 8 maçaneta com cremona; 2 com texto ambíguo.
- Módulo: 3.621 módulo único; 13 módulos separados; 2 vazios.
- Acabamentos: todos os 3.636 registros usam guarnição de 70 mm internamente e barra chata de 30 mm externamente.

Esse perfil de uso fundamenta o baseline da Fase 1: janela de uma folha, horizontal, módulo único, sem tela, sem bandeira e sem reforço estrutural adicional.

## Catálogo comprovado para o baseline

| Grupo | Código | Descrição | Preço legado |
| --- | --- | --- | ---: |
| Perfil PRIME | `PR4263` | Travessa usada como marco/folha | R$ 25,44/m |
| Marco DESIGN | `DE6058` | Marco alto de abrir | R$ 38,45/m |
| Folha DESIGN | `DE6078` | Folha janela abertura externa | R$ 45,44/m |
| Baguetes | `BA2516`, `BA2018`, `BA1816`, `BA1216`, `BA1016`, `BA0716`, `BA3518`, `BA3218` | Seleção pela espessura | Conforme `LISTAPERFIS!23:30` |
| Reforços | `RAG - PR4263`, `RAG - DE6058`, `RAG - DE6078` | Reforços internos | R$ 7,00; 8,00; 10,00/m |
| Acabamentos | `AC7012`, `AC3004` | Guarnição 70 mm; barra chata 30 mm | R$ 14,63; 3,24/m |
| Vedações | `ACB606`, `AC0002` | Borracha Prime 6×6; borracha Maxim-Ar | R$ 1,80; 1,60/m |
| Acessórios | `AC0312`, `AC0001` | Calço de vidro; tapa deságue | R$ 0,35; 1,00/un |
| Fechamento | `FEC4`, `MAC3`, `CRE17`–`CRE20`, `CON1` | Fecho/maçaneta/cremonas/contra-fecho | Conforme `LISTAFERRA!29:35` |
| Braços PRIME | `BRA1`–`BRA5` | Caixa 14 mm, DT10–DT24 | R$ 25,02 a 40,00/un |
| Braços DESIGN | `BRA6`–`BRA10` | Caixa 16 mm, DT10–DT24 | R$ 60,00 a 95,00/un |
| Parafusos | `PAR1`, `PAR2` | Ferragem; reforço | R$ 0,15; 0,10/un |

## Regras implementadas

| Regra | Excel | Fórmula/condição | Interpretação |
| --- | --- | --- | --- |
| `MX-GEO-001` | `D8:E9` | marco final = L/A; corte = final + `PFAB!B1` | Solda de 5 mm nos quatro cortes do marco |
| `MX-GEO-002` | `D10:E11` | PRIME = dimensão − 2×28 + 2×6; DESIGN = dimensão − 2×40 + 2×8; corte +5 | Folha base sem bandeiras |
| `MX-GEO-003` | `D12:E13` | baguete = folha − 2×44 PRIME ou −2×60 DESIGN | Vão interno da folha |
| `MX-VID-001` | `D59:I59` | vidro = baguete − `PFAB!B12`; área = L×A×qtd | Folga total de 8 mm em cada dimensão |
| `MX-BAG-001` | `B12:B13` | faixas condicionais pela espessura indicada no início da descrição | Baguete específica por sistema/espessura |
| `MX-REF-001` | `D42:I43` | marco − 2×44 PRIME; marco − 2×58 DESIGN | Reforço interno do marco |
| `MX-REF-002` | `D44:I45` | igual às dimensões das baguetes | Reforço interno da folha |
| `MX-ACA-001` | `D33:I34` | dimensão + `PFAB!B14` = +140 mm | Guarnição interna, duas peças por eixo |
| `MX-ACA-002` | `D35:I36` | dimensão + `PFAB!B15` = +60 mm | Barra chata externa, duas peças por eixo |
| `MX-VED-001` | `G67:I67` | 2×(baguete L + baguete A) | Borracha do vidro PRIME |
| `MX-VED-002` | `G68:I68` | 2×(folha L + folha A) | Borracha da folha PRIME |
| `MX-VED-003` | `G69:I69` | repete `G68` | Borracha do marco PRIME |
| `MX-ACE-001` | `G72:I72` | 2×quantidade de perfis horizontais da folha | Quatro calços por folha base |
| `MX-ACE-002` | `G73:I73` | igual a `G8` | Dois tapa-deságues por unidade |
| `MX-FER-001` | `B76:I76` | altura da folha: ≤500, ≤600, ≤800, ≤1000, >1000 | Braço DT10/12/16/20/24, caixa 14 PRIME ou 16 DESIGN |
| `MX-FER-002` | `B77:I77` | `FECHO 1 PONTO` → `FEC4`; demais → `MAC3` | Seleção por igualdade normalizada/exata |
| `MX-FER-003` | `B78:I79` | cremona selecionada + 2×`CON1` | Somente quando o fechamento é maçaneta com cremona |
| `MX-FER-004` | `G80:I80` | 4 parafusos por metro por face e por peça de marco/folha, usando medidas de corte | Consumo técnico fracionário de `PAR2` |
| `MX-FER-005` | `G81:I81` | braços×8 + (fecho/maçaneta/cremona/contra-fecho)×2 | `PAR1`: 10 no fecho simples; 16 no conjunto com cremona |

## Faixas de baguete

O Excel extrai a espessura pelos dois primeiros caracteres de `K2`. A Engine usa a espessura explícita do catálogo existente.

- PRIME: `<8 BA2516`; `8–11 BA2018`; `12–15 BA1816`; `16 BA1216`; `17–23 BA1016`; `24 BA0716`.
- DESIGN: `<8 BA3518`; `8–11 BA3218`; `12–18 BA2516`; `19–21 BA2018`; `22–25 BA1816`; `26–30 BA1216`; `31–33 BA1016`; `34 BA0716`.

Espessuras fora dessas faixas são rejeitadas; não há fallback inventado.

## Regras inventariadas, mas adiadas

- Múltiplas folhas e orientação vertical: `MX!G3:I3`, `D10:K11`.
- Travessas H/V: `MX!14:15`, com rebaixos `PFAB!B18:B19`.
- Bandeiras integradas e módulos separados: `MX!16:31` e `48:55`.
- Reforço estrutural adicional: `MX!32`, condicionado às bandeiras.
- Tela recolhível: `MX!64`, preço composto por largura, altura e unidade em `LISTADIV!C5:C7`.
- Cotas personalizadas e subdivisões: `V2:AK2`.

Essas regras permanecem fora da Fase 1 para evitar uma abstração prematura e exigem goldens próprios.

## Comportamentos estranhos e bugs do legado

### `LEGACY-MX-DESIGN-SEALING-OMITTED`

`MX!B67:B69` habilita todas as vedações somente quando `B10=LISTAPERFIS!A7`, isto é, somente PRIME. No DESIGN, o Excel retorna material e custo zero. Não há evidência suficiente para definir o material correto do DESIGN. A Engine preserva zero e emite alerta.

### `LEGACY-MX-SEPARATE-MODULE-REINFORCEMENT-TOTAL`

O total de reforços em `MX!I56` soma apenas `I42:I47`; os reforços de bandeiras em módulos separados, linhas 48–55, ficam fora do subtotal embora possam ter quantidade/custo. Não afeta o baseline e deverá ser decidido antes da Fase 2.

### Rótulos herdados incorretos

As colunas R e U continuam rotuladas como “Roldanas” e “Dobradiça”, mas na MX armazenam reforço estrutural e modo de módulos. A Engine não replica esses nomes ambíguos.

### Custos históricos não são golden atual

Algumas linhas antigas da ORCS guardam preços anteriores. Exemplos:

- ORCS 7: armazenado R$ 264,49; XLSM atual recalculado R$ 358,1772.
- ORCS 15766: armazenado R$ 344,00084; XLSM atual recalculado R$ 359,84084.
- ORCS 16942 e 18712 já coincidem exatamente com o recálculo atual.

Portanto, entrada real vem da ORCS, mas o esperado técnico é o resultado da versão atual do XLSM identificada pelo hash.

## Casos Excel × Engine

| ORCS | Configuração | Excel recalculado | Engine | Diferença |
| ---: | --- | ---: | ---: | ---: |
| 7 | PRIME, 680×690, qtd. 2, 4 mm Mini Boreal | 358,177200 | 358,177200 | 0 |
| 11 | DESIGN, 550×550, qtd. 2, 4 mm Mini Boreal | 378,126020 | 378,126020 | 0 |
| 24 | DESIGN, 1150×700, qtd. 2, 4 mm Mini Boreal | 645,068520 | 645,068520 | 0 |
| 16942 | PRIME, 800×800, qtd. 1, 4 mm Mini Boreal | 419,780400 | 419,780400 | 0 |
| 18712 | DESIGN, 600×600, qtd. 1, 4 mm Mini Boreal | 409,292520 | 409,292520 | 0 |
| 15766 | PRIME, 580×590, 8 mm laminado Mini Boreal | 359,840840 | 359,840840 | 0 |

O caso de ferragem com cremona deriva de ORCS 3194, removendo a bandeira inferior para isolar o baseline: Excel e Engine retornam R$ 1.074,431820.

## Modelo mínimo homologável

`MaximArConfiguration` contém somente largura, altura, quantidade, sistema de folha, vidro, fechamento/cremona e os dois acabamentos comprovados. Aplicação é sempre janela; uma folha, orientação horizontal e módulo único são características fixas desta versão, não opções falsas.

Versão: `MX_ENGINE_0.1.0`. A versão `CR_ENGINE_0.5.0` permanece inalterada.
