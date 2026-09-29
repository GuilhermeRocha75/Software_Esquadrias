# GR — Reverse engineering Fase 23

Status: **GR_ENGINE_0.23.0 — AUDITORIA DE COBERTURA APROVADA, COM PENDÊNCIAS REAIS**

## Objetivo

A Fase 23 audita toda a família GR gravada na planilha oficial antes de
declarar o motor concluído. Nenhuma fórmula técnica foi alterada: a v0.23
promove exatamente os resultados da v0.22 e publica um gate de cobertura
honesto para a API e para as próximas fases.

Fonte oficial:

- arquivo XLSM com SHA-256
  `96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`;
- aba ORCS lida diretamente como OpenXML, sem modificar a planilha;
- 1.684 registros GR;
- auditoria reproduzível em `tools/audit_gr_phase23.py`;
- snapshot sanitizado em `test_cases/gr_coverage_v0_23.json`.

Nenhum nome, contato, endereço, código de cliente, item ou local entra no
relatório.

## Inventário histórico

| Ramo | Evidência ORCS |
| --- | ---: |
| 1 folha | 1.484 |
| 2 folhas | 200 |
| Painel completo | 1.100 |
| Vidro inteiro | 465 |
| Superior vidro/inferior painel | 119 |
| Tela mosquiteira | 20 |
| Persiana | 67 |
| Bandeira inferior e/ou superior | 46 |
| Bandeira com subdivisão interna | 9 |
| Módulos separados | 0 |
| Reforço estrutural opcional | 0 |

Dos 119 casos mistos, três gravam explicitamente a cota da travessa. A Engine
já representa essa medida por `mixed_split_from_bottom_mm`, sem tratar AF como
grade da folha.

## Ramos resolvidos ou bloqueados por regra física

### Grade AF/AG na folha móvel

O ORCS 9155 grava `AF=4` e `AG=1` dentro da folha móvel. A confirmação física
do projeto determina que AF/AG não pertencem à folha móvel GR. O caso fica
explicitamente classificado como `PROHIBITED_PHYSICAL` e não será copiado para
a Engine.

Os ORCS 270, 285 e 3560 usam AF para a única travessa do modo misto. Esses
casos continuam modelados pelo campo próprio de divisão entre painel e vidro.

### Módulos separados e reforço estrutural

Não existe evidência GR histórica para módulos separados nem para reforço
estrutural opcional: 1.683 registros válidos usam módulo único e sem reforço;
o único restante é a linha ORCS 914, incompleta. Os dois recursos permanecem
fora da API com status `NO_HISTORICAL_EVIDENCE`, não como pendência oculta.

## Pendências reais encontradas

As contagens abaixo podem se sobrepor porque uma mesma linha pode exigir mais
de uma correção.

| Grupo | Registros afetados | Decisão |
| --- | ---: | --- |
| Aplicação independente do tipo de folha | 47 | Implementar sem voltar a acoplar `PORTA`/`JANELA` ao perfil da folha |
| Fechamento incompatível com o gate atual da aplicação | 66 | Separar a escolha de ferragem da aplicação e homologar BOM |
| Fechamentos especiais fora do vocabulário atual | 18 | Mapear por evidência física ou manter bloqueio explícito |
| Combinações de bandeira fora da v0.22 | 21 | Homologar por topologia, tela e número de folhas |
| Vidros históricos ausentes do catálogo atual | 24 | Cadastrar com código, espessura e preço rastreáveis |
| Dobradiça pérnio ou valor inválido | 5 | Homologar o pérnio ou bloquear cada caso com justificativa física |

As linhas ORCS 543 e 914 também exigem saneamento de origem: a primeira contém
um tipo de folha digitado incorretamente; a segunda registra aplicação
`HORIZONTAL` e omite módulo e reforço.

## Correções do contrato da API

A rota `/api/v1/engine/gr/options` agora:

- publica `phase=23` e `GR_ENGINE_0.23.0`;
- expõe o inventário e o gate em `coverage_audit`;
- não declara mais `open_questions=[]` nem aprovação antiga da Fase 20;
- informa 20 casos históricos de tela, conforme a ORCS oficial;
- classifica grade na folha como proibida fisicamente;
- classifica módulos separados e reforço estrutural como sem evidência;
- mantém compra/corte bloqueado.

## Gate técnico

O estado correto após esta fase é:

- `historical_coverage_closed=false`;
- `purchase_plan_supported=false`;
- `main_ready=false`;
- `status=FASE_23_AUDITADA_COM_PENDENCIAS_REAIS`.

Portanto, a GR ainda não deve ser integrada à `main`. A próxima fase precisa
resolver primeiro os ramos históricos reais; compra/corte vem depois da
homologação dessas combinações.

## Validação candidata

- auditoria do XLSM contra o snapshot: verde;
- Engine completa: 318 testes verdes;
- API completa: 63 testes verdes;
- Web: build Vite verde;
- commit candidato: `2ce91da7ab459a4c85584e2d7ee999f2dca9fa68`;
- GitHub Actions: execução 239 verde no commit candidato;
- `main`: intacta.
