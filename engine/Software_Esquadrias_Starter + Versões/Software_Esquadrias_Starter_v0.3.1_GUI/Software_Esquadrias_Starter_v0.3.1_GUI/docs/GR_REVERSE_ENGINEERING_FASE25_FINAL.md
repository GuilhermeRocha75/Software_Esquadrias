# GR — Fase 25 final

Status: **GR_ENGINE_0.25.0 — MIGRAÇÃO GR CONCLUÍDA**.

## Fonte e critério

- fonte funcional: `SOFTBETA_ PERFIL PRE DELL AMANDA(1).xlsm`;
- SHA-256: `96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`;
- universo auditado: **1.684** registros GR da aba `ORCS`;
- fórmulas, catálogos e combinações históricas foram lidos diretamente do OpenXML;
- correções físicas já comprovadas prevalecem sobre defeitos conhecidos da planilha;
- dados ausentes não recebem preço ou kit inventado.

A auditoria que antecedeu a implementação permanece documentada em
`GR_REVERSE_ENGINEERING_FASE25_AUDITORIA.md`. Este documento registra o
fechamento da implementação.

## Escopo consolidado

A versão final preserva todas as regressões das Fases 1 a 24 e consolida:

- porta e janela, com aplicação comercial independente do tipo físico da folha;
- uma ou duas folhas;
- painel completo, vidro inteiro e modo misto nas folhas físicas compatíveis;
- bandeira inferior, superior ou ambas, simples ou com divisões verticais;
- tela recolhível e os quatro modos de persiana GR comprovados;
- dobradiça 90 mm, Sistema OB e dobradiça pêrnio;
- fechaduras mono/multiponto e fechamentos com cremona;
- plano de compra e corte integrado ao pedido unificado.

## Decisões encerradas na Fase 25

### Cremona

A cremona é uma seleção explícita de cada orçamento. As opções standard
`CRE1` a `CRE16` e as opções Oscilo/Giro `CRE21` a `CRE24` vêm da
`LISTAFERRA`. A `CRE12` de 800 mm permanece apenas como fallback para carregar
orçamentos legados que não gravaram a seleção.

### Fechadura de janela

Folha física de janela com fechadura mono ou multiponto usa a fechadura sem
chave e sem cilindro. O comprimento pode ser informado em
`window_lock_length_mm`; a interface o exige nos novos orçamentos.

### Dobradiça pêrnio

A opção comercial é exposta como `DOBRADIÇA PÊRNIO` e resolve para o item
`DOB5` da `LISTAFERRA`. A quantidade vem de `GR!G105`: **3 por folha**. Os
parafusos seguem `GR!G119`: **8 PAR1 por dobradiça**, somados aos parafusos do
fechamento.

### Vidros fora da LISTAVIDROS

Variações textuais inequívocas são ligadas à linha equivalente já cadastrada.
Qualquer outro vidro livre exige descrição, código, espessura e preço por m²
no orçamento. Assim, os 24 registros históricos sem correspondência direta
continuam calculáveis sem inventar preço.

### Matriz restante

A fórmula `G5=2` foi generalizada para janela GR de duas folhas. Bandeiras
integradas seguem os campos `AA`, `AB`, `AH` e `AJ` do XLSM, com um vidro por
vão e reforço/parafusos das travessas calculados na Engine. Divisões
horizontais continuam bloqueadas porque não existem na ORCS oficial.

## Exceções manuais, não bloqueadoras

- **11 registros inválidos/incompletos** na fonte permanecem fora da automação;
- **7 fechamentos especiais** sem kit e preço completos devem ser lançados
  como item manual;
- travessas dentro da folha móvel continuam fisicamente proibidas;
- módulos separados e reforço estrutural opcional continuam indisponíveis por
  ausência de casos GR na ORCS.

Essas exceções não são variantes automáticas do modelo GR e, por isso, não
mantêm o gate técnico aberto.

## Integração

- Engine: `GR_ENGINE_0.25.0` e `GR_COVERAGE_AUDIT_0.25.0`;
- API: cálculo, opções e endpoint `/api/v1/engine/gr/purchase-plan`;
- pedido unificado: aceita itens `family=GR`;
- interface: cadastro/edição do Giro GR, incluindo cremona por orçamento,
  pêrnio, fechadura de janela, vidro personalizado, bandeiras, tela e persiana;
- gate: `FASE_25_FINAL_CONCLUIDA`, cobertura histórica fechada e
  `main_ready=true`.

## Verificação

As suítes da Engine e da API preservam os goldens anteriores e cobrem as novas
regras. Uma auditoria combinatória adicional exercita tipos de folha, uma/duas
folhas, os fechamentos, as três dobradiças, bandeiras, tela e persiana. O build
de produção da interface também faz parte do aceite desta fase.
