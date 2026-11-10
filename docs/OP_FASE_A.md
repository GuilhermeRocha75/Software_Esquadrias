# Ordem de Produção — contrato e relatório técnico da Fase A

Estado: **implementado para auditoria independente; NÃO homologado**.
Escopo: dados, Engine, serviço, contratos Pydantic, preview JSON e testes.
PDF, imagens renderizadas e Web permanecem fora desta entrega.

## Implementação e limites

`esquadrias_engine.production` projeta os resultados homologados de CR,
MAXIM_AR, GR e FX em dataclasses imutáveis. Não altera geometria, BOM, preços,
custos, compra ou fórmulas existentes. A API converte entradas usando exatamente
as mesmas funções dos endpoints anteriores, extraídas para `configurations.py`.
O serviço calcula cada item, chama a projeção e adiciona snapshots/validações.
PV e GD são rejeitadas; `MX` é somente a identificação da fixture legada,
convertida explicitamente para `MAXIM_AR` na reconstrução de testes.

Cada linha conserva posição, grupo, utilização, código, descrição, unidade
comercial, medidas, quantidades originais e origem da BOM. Não há consolidação,
ordenação por código, exclusão de linhas sem descrição ou agrupamento que
desloque linhas intercaladas. `lines.position` é a posição na Engine.
**A correspondência exata com a sequência impressa POP/OP ainda exige auditoria
da fonte privada**, indicada por `LEGACY_LAYOUT_UNVERIFIED`. Não se declara
reprodução integral da ordem impressa apenas com uma fixture parcial.

Medidas finais de marco/folha são lidas de `geometry`; bandeiras CR/MX usam
`fixed_panels`. As demais medidas comprovadas sem acréscimo de solda têm uma
lista explícita de roles, fundamentada nas chamadas dos calculadores existentes.
Uma nova role não recebe automaticamente `final = corte`.
FX!E20/E21 = D20/D21 + 5: somente a representação final dos reforços foi
acrescentada, com regressão contra D/E do snapshot e dos golden FX existentes.
O marco vertical GR mantém sua tolerância própria (por exemplo 2110/2113),
sem usar um desconto genérico de 5 mm.

Contagem física e unidade comercial são distintas. Perfis usam `quantity_unit`
`piece` e `material_unit` `m`; vidro usa peças e `m²`. Vedações agregadas usam
`run`: quantidade de conjuntos de consumo com comprimento total por produto,
sem sugerir cortes individuais. Fator de área original da tela permanece em
`bom_quantity_*`; a contagem de recortes físicos usa `screen_frame_count`
validado na Engine, inclusive para 3 folhas e para cada célula de grade.
`PANEL_FILL`/`LOWER_PANEL_FILL` mantêm frações, unidade comercial `m` e contagem
`unresolved`, com erro técnico explícito. Parafusos fracionários são preservados
com `piece`/`un` e pendência de confirmação. O adaptador não arredonda nada.

## Interface HTTP

`POST /api/v1/production-orders/preview`

Recebe `ProductionOrderRequest`, retorna `ProductionOrder` (HTTP 200).
Erros de schema, famílias não suportadas e configurações impossíveis retornam
422. Erros da Engine identificam o item. Pendências técnicas/assets não eliminam
linhas nem impedem o preview: aparecem em `validations` e nos indicadores de
completude. O preview não é liberação para fabricar.

Exemplo mínimo sem dados pessoais:

```json
{
  "company_id": "00000000-0000-0000-0000-000000000001",
  "order_id": "ANON-001",
  "items": [{
    "item_id": "item-1",
    "finish_key": "BRANCO",
    "technical_input": {"family": "FX", "width_mm": 1200, "height_mm": 1000}
  }],
  "stock_lengths_mm": {"DE6058": 5900}
}
```

Nenhum comprimento padrão é fixado no contrato. O mapa opcional é por material
e deve vir da configuração da empresa. Peças excedentes ficam inteiras:
`MANUAL_SPLICE_REQUIRED` para FX, coerente com a regra existente; demais famílias
recebem `REQUIRES_ENGINEERING_REVIEW`. Não se inventam segmentos ou emendas.
O preview funciona sem mapa; nesse caso não declara avaliação contra estoque.

`company_id` é contexto obrigatório em todos os documentos e índices de assets.
Não há persistência nem consultas a dados de outras empresas. Um índice injetado
de outra empresa é rejeitado. Esta fase não acrescenta autenticação; quando
houver persistência, a identidade autenticada deverá controlar o contexto.

## Schemas públicos — todos os campos

`OPModel` é a base fechada (`extra=forbid`), frozen, sem NaN/infinito. As entradas
de OP herdam os campos e defaults dos requests existentes em
`api/app/schemas.py`, sem alterar esses contratos anteriores. A documentação
estrutural integral também está disponível no OpenAPI `/openapi.json` e `/docs`.

| Modelo / interface | Campos e significado |
| --- | --- |
| `ProductionOrderRequest` | `company_id` UUID obrigatório; `order_id` identificador; `items` sequência não vazia com IDs únicos; `stock_lengths_mm` mapa opcional de comprimentos finitos positivos por código |
| `ProductionOrderItemRequest` | `item_id` identidade estável; `finish_key` descritor de cor/acabamento para assets (não muda a engenharia); `technical_input` união discriminada por `family` explícita |
| `OPCRInput` | Herda CR: `family`, `width_mm`, `height_mm`, `quantity`, `leaf_count`, `leaf_system`, `application`, `glass_description`, `closure_mode`, `cremona_base`, `roller_description`, `internal_finish`, `external_finish`, `screen_enabled`, `shutter_enabled`, `shutter`, `leaf_grid`, `bottom_fixed_panel`, `top_fixed_panel`, `structural_reinforcement` |
| `OPMaximArInput` | Herda MX: `family`, `width_mm`, `height_mm`, `quantity`, `leaf_count`, `orientation`, `module_mode`, `leaf_system`, `glass_description`, `closure_mode`, `cremona_description`, `internal_finish`, `external_finish`, `screen_enabled`, `leaf_grid`, `bottom_fixed_panel`, `top_fixed_panel`, `structural_reinforcement`, `sealing` |
| `OPGrInput` | Herda GR: `family`, `width_mm`, `height_mm`, `quantity`, `leaf_count`, `leaf_system`, `application`, `panel_mode`, `glass_description`, `mixed_split_from_bottom_mm`, `module_mode`, `closure_mode`, `cremona_description`, `hinge_description`, `window_lock_length_mm`, `custom_glass_code`, `custom_glass_unit_price`, `custom_glass_thickness_mm`, `shutter`, `screen_enabled`, `top_flag_height_mm`, `bottom_flag_height_mm`, `bottom_flag_vertical_transoms`, `bottom_flag_horizontal_transoms`, `top_flag_vertical_transoms`, `top_flag_horizontal_transoms`, `internal_finish`, `external_finish` |
| `OPFixoInput` | Herda FX: `family`, `width_mm`, `height_mm`, `quantity`, `vertical_transoms`, `horizontal_transoms`, `glass_description`, `internal_finish`, `external_finish` |
| `OPCustomDimension` | `axis`, `index`, `clear_span_mm`: cota de vão no eixo/índice |
| `OPLeafGrid` | `horizontal_transoms`, `vertical_transoms`, `custom_dimensions`: subdivisões e cotas |
| `OPFixedPanel` | `height_mm`, `horizontal_transoms`, `vertical_transoms`: bandeira e divisões |
| `OPReinforcement` | `material_code`: reforço selecionado |
| `OPSealing` | `internal_material_id`, `description`, `unit_price_per_meter`: configuração técnica MX existente |
| `OPShutter` | `mode`, `box_description`, `slat_description`: configuração explícita existente de persiana |
| `TechnicalInput` | Alias da união `OPCRInput / OPMaximArInput / OPGrInput / OPFixoInput` |

`quantity` do produto é inteiro estrito positivo; bool não é aceito como número.
Entradas aninhadas também rejeitam campos desconhecidos e não finitos.
As regras de compatibilidade geométrica continuam na Engine.
Preços exigidos por configurações técnicas existentes (vedação/vidro customizado)
ficam no snapshot integral dos inputs. Não são expostos totais comerciais,
custos calculados, plano de compra nem orçamento no documento de OP.

| Saída | Campos e significado |
| --- | --- |
| `ProductionOrder` | `schema_version=OP_0.1.0`; `company_id`; `order_id`; `request_snapshot_json` JSON canônico integral; `snapshot_sha256` hash do documento excluindo o próprio hash; `items`; `validations`; `technical_data_complete`; `assets_complete`; `audit_status=PENDING_INDEPENDENT_AUDIT` |
| `ProductionOrderItem` | `item_id`; `position` ordinal no pedido; `family`; `finish_key`; `input_snapshot_json` inputs efetivos incluindo defaults; `engine_version`; `technical_contract_version`; `model_description`; `lines`; `assets` |
| `ProductionOrderLine` | `position` ordinal na BOM; `group` categoria; `utilization` role; `code`; `description`; `material_unit` unidade comercial; `quantity_unit` (`piece/run/consumption_factor/unresolved`); `quantity_per_unit` e `quantity_total` contagens para OP; `bom_quantity_per_unit` e `bom_quantity_total` valores originais; `final_length_mm`; `cut_length_mm`; `width_mm`; `height_mm`; `source` origem; `measurement_basis` fundamento do final; `splice_status` pendência de comprimento |
| `ProductionValidation` | `code`; `severity=error/warning`; `item_id`; `field`; `message`; `position` opcional da BOM |
| `ProductionAssetReference` | `kind=MODEL_SKETCH/FRAME_SECTION/LEAF_SECTION/PROFILE_SECTION`; `key`; `status=AVAILABLE/MISSING_ASSET/MISSING_TECHNICAL_DATA`; `relative_path` e `sha256` opcionais |

As saídas têm apenas valores imutáveis (tuplas, modelos frozen e JSON textual).
Snapshots ficam independentes das listas/dicionários mutáveis recebidos.
Reimpressão futura deve carregar o documento salvo, sem recalcular com uma
Engine mais nova. O hash inclui versões, medidas, inputs e referências de assets;
é uma impressão digital determinística, não assinatura/autenticação. Não se
implementou armazenamento/versionamento de OP nesta fase.

`technical_data_complete` significa ausência de `MISSING_TECHNICAL_DATA`;
não substitui auditoria nem resolve `LEGACY_LAYOUT_UNVERIFIED`.
`assets_complete` exige todas as referências disponíveis no índice.

## Interfaces Python públicas

| Interface | Contrato |
| --- | --- |
| `engine.production.PRODUCTION_CONTRACT_VERSION` | Constante `OP_TECHNICAL_0.1.0` |
| `ProductionIssue` | Dataclass frozen: `code`, `field`, `message`, `position` opcional |
| `ProductionLine` | Dataclass frozen com os mesmos campos de `ProductionOrderLine` |
| `ProductionItemData` | Dataclass frozen: `family`, `engine_version`, `contract_version`, `model_description`, `lines`, `issues` |
| `build_production_item(family, result, *, stock_lengths_mm=None)` | Recebe `CalculationResult`, devolve `ProductionItemData`; rejeita família/versão incompatíveis, comprimentos inválidos e valores técnicos não finitos/negativos; preserva resultado original |
| `production_service.canonical_json(value)` | JSON canônico com ordenação de chaves, UTF-8, sem NaN/infinito |
| `build_production_order(request, *, asset_index=None)` | Devolve `ProductionOrder`; recalcula com Engine atual somente na construção; revalida entrada e rejeita índice de outra empresa; ValueError identifica input técnico inválido |
| `main.preview_production_order(payload)` | Handler do POST; converte ValueError para HTTP 422 |
| `ProductionAsset(key, relative_path, sha256)` | Dataclass frozen de metadados; valida chave, caminho relativo e hash hexadecimal de 64 caracteres |
| `ProductionAssetIndex(company_id, entries=())` | Dataclass frozen com entradas de uma única empresa e chaves únicas |
| `ProductionAssetIndex.find(key)` | Lookup exato; retorna `ProductionAsset` ou None |
| `tools.compare_op_golden.compare_case(case, reconstruction)` | Retorna comparação por campo, valores PDF/Engine, fonte/página, classificação, hipóteses, inputs e validações |
| `build_report()` | Carrega fixture/reconstruções e agrega os 12 casos; rejeita IDs incompatíveis |
| `report_markdown(report)` | Gera relatório com todos os valores por campo e premissas |
| `main()` do comparador | CLI com `--output-dir`; grava JSON/Markdown anonimizados e imprime contagens |

## Assets e dados técnicos ausentes

O índice é fornecido pelo servidor ao serviço; o endpoint atual usa índice vazio.
Não se abre disco, URL, RAR ou PDF para localizar arquivos. `AVAILABLE` significa
metadados registrados, sem afirmar que bytes/hashes foram verificados; essa
verificação e o armazenamento de imagens pertencem à Fase B.

Chave de modelo: `model/{family}/{sha256-do-input-canônico}/{finish_key}`.
O hash usa os inputs completos; alteração de qualquer input exige novo registro
ou alias explícito na futura gestão de assets. Chave de perfil:
`profile/{code}/{finish_key}`. Um arquivo pode atender mais de um tipo de seção.
Nenhum perfil, croqui ou código visual é inventado.

Código existente no catálogo, sem registro de imagem: `MISSING_ASSET`.
Código/descrição/unidade ausente, perfil desconhecido ou cor não informada:
`MISSING_TECHNICAL_DATA`. A linha original é mantida para revisão. Caminhos
absolutos, Windows, URLs, `..`, segmentos vazios ou `.` são rejeitados no índice.

## Golden parciais e pendências de fábrica

Relatórios reproduzíveis: [Markdown](audits/op_fase_a/op_golden_comparison.md)
e [JSON](audits/op_fase_a/op_golden_comparison.json). Contêm fonte, página,
campo, valor do PDF, valor da Engine, motivo e inputs de comparação.

- **129/129 campos da fixture parcial iguais**, sob os inputs reconstruídos.
- **14 verificações suplementares** da especificação: 12 iguais, 2 divergentes.
- **10 casos iguais no escopo parcial; 2 com input insuficiente** para concluir
  o conjunto de persiana. Nenhum caso é declarado uma OP integralmente validada.
- OP2 p2: talas PDF **40,25**, Engine **41** na hipótese de painel único;
  comprimento **1346 mm** igual. A correção física já pertence à Engine CR.
- OP3 p1: talas PDF **59**, Engine **60** na hipótese de dois painéis;
  comprimento **933 mm** igual. A regra existente arredonda por painel.
- Faltam acionamento/arranjo/eixos originais dos dois casos. As hipóteses da
  fixture de reconstrução não autorizam selecionar ferragens para fabricação.
- GR op p3: painel PDF **12,8357143**, Engine **12,835714285714285**. Igual dentro
  de 1e-6 de precisão de transcrição; unidade física permanece pendente.
- Parafusos fracionários: confirmar quantidade de instalação e unidade, sem
  arredondamento do adaptador. Linhas vazias/código 0 permanecem sinalizadas.
- O divisor sem código de OP3 está documentado na fonte, mas não é criado na
  BOM por palpite. O contrato/teste de linha vazia preserva a anomalia se fornecida
  por resultado técnico; falta comprovar sua seleção e identificação corretas.
- `op.pdf` informa workbook diferente nos metadados. Confirmar versão contra a
  fonte técnica de referência antes de extrapolar a igualdade parcial.
- FX tem caso próprio, regressão D/E contra snapshot e golden históricos; ainda
  falta uma OP real anonimizada para verificar a apresentação de fábrica.

Para renderização fiel ainda faltam arquivos de croquis/seções por cor com hash
verificado, comprovação da sequência POP/OP, decisão de representação/unidade
para frações físicas e inputs completos dos casos citados. Cabeçalhos comerciais
de cliente/obra não foram introduzidos nesta fase de dados técnicos; sua origem e
isolamento deverão ser definidos antes de preencher o cabeçalho completo da OP.

## Reproduzir verificações

Execução local em 05/11/2026, Python 3.13.17:

| Suíte | Base anterior | Resultado final | Novos testes |
| --- | --- | --- | --- |
| Engine ativa, suite completa | 365 passando | **381 passando** | 16 |
| API, suite completa | 75 passando | **108 passando** | 33 |
| Total | 440 | **489 passando, zero falhas** | 49 |

Os 12 casos parciais são 12 métodos de teste individuais, além das verificações
de cobertura e de detecção de uma divergência injetada. Os 66 casos congelados
de FX são subcasos do teste de finais/cortes; não são somados artificialmente à
contagem de métodos. Foram verificados também JSON round-trip, isolamento de
índice de assets, validação HTTP 200/422, ausência de custos/compra na saída
técnica, schema OpenAPI e YAML do workflow. `git diff --check` passou.
O ambiente emite aviso de depreciação da integração httpx/TestClient da versão
instalada de Starlette; os testes passam e o aviso não foi suprimido.

Na raiz, com o ambiente virtual ativo:

```powershell
python -m pip install -r api/requirements-dev.txt
python -m unittest discover -s "engine/Software_Esquadrias_Starter + Versões/Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI/tests"
python -m unittest discover -s api/tests
python tools/compare_op_golden.py --output-dir docs/audits/op_fase_a
```

A CI existente inclui a branch de OP, instala dependências de teste e compara
os relatórios gerados com os versionados. Nenhum arquivo privado foi adicionado.
O escopo implementado está pronto para auditoria independente da Fase A;
o avanço à Fase B depende dessa auditoria e das decisões acima. Não há liberação
automática para fabricação, homologação ou merge na main.

## Arquivos desta entrega

Modificados:

- `.github/workflows/ci-software-esquadrias.yml`: branch de OP, dependências e evidência reproduzível.
- `api/README.md`: endpoint e documentação de OP.
- `api/app/main.py`: preview JSON e uso das conversões compartilhadas.
- `docs/ORDEM_PRODUCAO_V1.md`: estado da Fase A e link do contrato.

Criados:

- `api/app/configurations.py`: conversões existentes extraídas sem alterar suas funções.
- `api/app/production_assets.py`: índice de metadados por empresa.
- `api/app/production_schemas.py`: schemas Pydantic de entrada/saída.
- `api/app/production_service.py`: orquestração de pedidos mistos e snapshots.
- `api/requirements-dev.txt`: dependência do cliente de testes HTTP.
- `api/tests/fixtures/op_reference_inputs.json`: reconstruções e premissas explícitas.
- `api/tests/test_op_golden.py`: 12 referências e testes do comparador.
- `api/tests/test_production_orders.py`: serviço, contratos, assets e HTTP.
- `docs/OP_FASE_A.md`: este relatório/contrato.
- `docs/OP_FASE_A_MAPEAMENTO.md`: inspeção de dados e lacunas antes da implementação.
- `docs/audits/op_fase_a/op_golden_comparison.json`: evidência por campo, validações e inputs.
- `docs/audits/op_fase_a/op_golden_comparison.md`: evidência legível por caso/página.
- `tools/compare_op_golden.py`: comparador reproduzível.
- `engine/Software_Esquadrias_Starter + Versões/Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI/src/esquadrias_engine/production.py`: contrato/projeção técnica.
- `engine/Software_Esquadrias_Starter + Versões/Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI/tests/test_production.py`: regressões da projeção.
