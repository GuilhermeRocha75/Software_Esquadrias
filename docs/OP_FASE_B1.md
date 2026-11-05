# Ordem de Produção — Fase B1

Infraestrutura implementada para **nova auditoria independente**. A autorização
do proprietário informa aprovação da base da Fase A com ressalvas; isso não
constitui homologação automática desta entrega nem autorização para fabricar.
Branch exclusiva: `feature/ordem-producao-v1`. Não há PDF renderizado ou mudança
na Web. Nenhum arquivo da Engine ou fórmula homologada foi alterado.

## Fontes efetivamente acessadas

Foram lidos localmente a planilha de SHA-256
`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`,
o módulo VBA `OP1.OP_1`, os três PDFs `op.pdf`, `OP 2.pdf`, `OP 3.pdf` e as pastas
`CROQUIS`/`CROQUIS_PERFIS`. Outra cópia local da planilha tem SHA diferente e não
foi usada. Nenhuma macro foi executada e nenhum original foi modificado.

Os 12 PDFs/páginas usam retrato, aproximadamente 595,32 × 841,92 pt. A análise
confirmou as colunas de cabeçalho/tabelas, os nomes de croquis e a sequência
de utilizações. O extrator público exporta exclusivamente labels técnicos e
códigos reconhecidos depois do cabeçalho da tabela: **376 linhas de referência**.
Não exporta cabeçalhos de clientes, descrições livres, caminhos, texto integral,
VBA ou arquivos originais. A evidência continua parcial, não uma transcrição
integral de medidas/quantidades dos PDFs.

Evidências versionadas:

- [Âncoras das quatro famílias](../api/app/data/op_legacy_order_v1.json): linhas A8:A200 da fonte oficial.
- [Sequências das 12 páginas](../api/tests/fixtures/op_layout_reference_v1.json): fonte/página, SHA do PDF, dimensões e utilizações/códigos técnicos.
- [Comparação da apresentação](audits/op_b1/layout_comparison.json): posições Engine/impressão/referência e diferenças.
- [Inventário sanitizado da importação real](audits/op_b1/image_inventory.json): recursos exatos, contagens e limites da evidência visual.

## Imagens: identificação e armazenamento

O nome de modelo é uma identidade de **topologia**, independente de largura,
altura, quantidade, preço, vidro comercial e ferragens. Inclui família, sistema
de folha, aplicação, folhas, orientação/modo de módulos, tela/persiana,
preenchimento e subdivisões de folhas/bandeiras. Não há cálculo de engenharia
nessa identificação. Entradas são normalizadas pelos schemas existentes.

`model_identity(inputs, finish)` produz chave `família/hash-da-topologia` e o
basename técnico exato do legado. O acabamento é normalizado em Unicode NFC,
sem trocar uma cor por outra. A resolução exige correspondência exata de modelo
e acabamento. Modelo/arquivo ausente não recebe imagem genérica, outro modelo,
cor branca ou sentinela `0.jpg` como substituto.

Perfis são identificados por código de catálogo e acabamento. O VBA original
usa `Croquis_perfis/{código}.jpg`, sem cor: o manifest permite essa reutilização
somente com a política explícita `NEUTRAL_LEGACY_SECTION`. Croquis de modelos
sempre exigem política `EXACT`. A política neutra não se aplica a modelos.

Os bytes originais são copiados sem edição para `objects/{sha256}.{ext}` em
armazenamento privado. O importador e a leitura conferem:

- SHA-256, formato raster JPEG/PNG/WebP, decodificação e dimensões;
- limite de 20 MB por arquivo e 25 milhões de pixels;
- contenção na raiz configurada, inclusive após resolução de symlinks;
- rejeição de caminhos absolutos, travessia, URLs e identidades duplicadas;
- isolamento pelo `company_id` do manifest e do documento.

Foram importados **25 vínculos reais: oito modelos e 17 perfis**, sem vínculos
solicitados ausentes. As pastas de origem possuem 1.504 arquivos de imagem de
croquis inventariados e 25 JPGs de perfis. Foram selecionados os sete modelos
das referências e o modelo próprio de FX; os 17 perfis pertencem ao catálogo
atual. Sentinela e códigos de famílias/identificações não suportadas não foram
convertidos por palpite. Os nomes exatos necessários estão no inventário JSON.
Não se importou toda a biblioteca indiscriminadamente.

As imagens dos 36 slots principais das referências (croqui, marco, folha em
12 páginas) foram resolvidas e verificadas localmente. As imagens das quatro
primeiras linhas de perfis também têm slots próprios, conforme o VBA. FX não
recebe seção fictícia de folha. Os demais perfis ficam disponíveis no manifest,
sem exigir imagens em linhas que o original não ilustra.

**Limite visual:** verificar os JPGs importados não comprova identidade visual
com os bitmaps incorporados aos PDFs. Uma comparação pontual de pixels não
coincidiu; a causa não foi classificada. Auditoria visual, enquadramento, escala,
compressão e eventual diferença de versão permanecem para a renderização
posterior. Não se declara paridade visual nem se criam imagens substitutas.

## Ordenação POP/OP e montagem de blocos

O VBA copia A1:F200 da família para POP, remove linhas cuja quantidade é zero/
vazia e copia o buffer de impressão para OP. O buffer legado A1:F80 é uma
limitação antiga que não é reproduzida como truncamento na infraestrutura nova.

`production_ordering.py` associa roles da Engine às linhas técnicas da planilha.
Referências de célula disponíveis em `source` são usadas como complemento.
Ordena-se globalmente por âncora da planilha, com desempate estável pela posição
da Engine. Não se ordena por código nem se reagrupa toda uma categoria.

Diferenças de sequência resolvidas incluem:

- CR: baguetes antes de interlock/trilhos;
- CR: caixa/guias/talas antes dos reforços;
- CR: borracha da folha antes da borracha da tela;
- GR: vedações na posição da planilha, antes de acessórios/ferragens;
- parafusos no final de cada família, sem antecipar PAR2 por sua posição na BOM.

Cada linha de apresentação conserva `engine_position`, `legacy_sheet`,
`legacy_row`, `print_position` e a linha técnica original completa. `group`
continua sendo a categoria original da Engine. Blocos são trechos **contíguos**
da sequência já ordenada, por tipo de tabela: cortes, superfícies, consumíveis,
acessórios, ferragens, parafusos e extensões. Um grupo intercalado não é movido
para juntar blocos. Há metadados de continuação e repetição de colunas.

Linhas novas sem âncora ficam visíveis em `ENGINE_EXTENSION`, com finding
`UNMAPPED_LEGACY_ROW`. Grades dinâmicas preservam todas as linhas por âncora,
mas rótulos A/B/C e subdivisões precisam de OP própria: recebem
`DYNAMIC_LAYOUT_REVIEW` e `PARTIALLY_MAPPED`. Um teste cobre mais de 80 linhas.
Nenhuma linha da Engine, inclusive sem descrição/código ou com quantidade
fracionária, é removida para reproduzir a aparência do Excel.

## Resultado das comparações

Nos 12 casos, a ordem relativa das **342 linhas comuns** coincidiu. Foram
preservadas **355/355 linhas da Engine**. Os 12 basenames de croquis coincidiram
com os nomes impressos nas referências. `SOURCE_ORDER_MAPPED` significa que
as linhas têm âncora, não que toda a OP coincida com o PDF.

O relatório enumera também **13 linhas adicionais da Engine, 34 linhas dos PDFs
sem correspondência e 26 diferenças de código**. Não foram ocultadas nem
corrigidas automaticamente. Principais explicações/pendências:

- Os inputs reconstruídos da Fase A usam `SEM ACABAMENTO` no CR; isso deixa
  ausentes as quatro linhas de arremate presentes em cada referência CR.
- Fechamentos/vidros/cremonas/roldanas não foram transcritos integralmente na
  fixture original. Os defaults reconstruídos não demonstram paridade desses
  códigos. GR também tem diferenças de kit que exigem inputs originais.
- Vedações acrescentadas pela Engine homologada aparecem em GR/MX, mesmo
  quando ausentes no PDF. Sua posição segue as linhas técnicas da fonte.
- OP3 tem linhas de divisor/eixos independentes que não coincidem com a hipótese
  de eixo único usada na Fase A. A nova inspeção reforça a necessidade de obter
  o modo original; não alterou silenciosamente a fixture ou o cálculo.
- A linha legada de divisor com código `0` não é inventada no documento técnico.
  A diferença permanece registrada na comparação de códigos/linhas.

As duas divergências anteriores de talas permanecem: **40,25 no PDF × 41 na
Engine**, e **59 × 60**, sob as hipóteses registradas. Painel GR
**12,8357143 × 12,835714285714285** continua fracionário, com unidade física
pendente. Parafusos fracionários também não são arredondados. O comparador da
Fase A e seus resultados são preservados.

## Cabeçalho e contrato de apresentação

`ProductionLayoutContext` recebe código/nome do cliente, código/nome da obra e
rótulos de item, vinculado a `company_id`. Largura, altura e quantidade vêm do
snapshot técnico. Campo privado ausente fica null e gera `MISSING_HEADER_DATA`;
não se extrai automaticamente o nome real dos PDFs. IDs de item desconhecidos,
duplicados, texto vazio/controle e contexto de outra empresa são rejeitados.

O plano mantém as colunas originais `Cód. Cliente | Nome | Item | Largura |
Altura | Quant.` e reserva código/nome de obra como dado complementar. Cada
item tem intenção de página A4 retrato e regiões ordenadas: imagens, cabeçalho,
descrição, blocos e pendências. Paginação física, tipografia, coordenadas finais
e renderização ainda não foram implementadas.

Medidas finais e de corte ficam em campos/colunas distintos. Vidro/tela usam
largura/altura. Quantidade física e unidade comercial continuam separadas.
Consumos agregados `run` mantêm comprimento e quantidade de conjuntos; recebem
`CONSUMPTION_PRESENTATION_REVIEW`. Sua conversão para a coluna de consumo do
legado ainda deve ser definida, sem apresentar um conjunto como uma peça ou
introduzir novas fórmulas técnicas na API.

O plano é frozen e inclui hashes do snapshot técnico, manifest, cabeçalho e
documento de apresentação. `build_production_layout` verifica o hash técnico e
não chama a Engine: pode preparar a reimpressão de uma OP salva. O hash não é
assinatura digital. Persistência e autorização de cliente/obra não fazem parte
desta etapa; dados de cabeçalho entram somente no request/response privado.

## Interfaces e integração

`POST /api/v1/production-orders/layout-preview` recebe
`{production_order: ProductionOrderRequest, context: ProductionLayoutContext}`.
Retorna `ProductionLayoutDocument`; 422 para entrada/contexto inválidos; 503
genérico para configuração de armazenamento indisponível, sem revelar paths.
Ausência de imagens produz metadados `MISSING_ASSET`, sem substituto visual.
O endpoint antigo de preview da Fase A conserva seu contrato e comportamento.

Configuração do servidor: `OP_IMAGE_MANIFEST` aponta para o manifest privado;
`OP_IMAGE_STORAGE_ROOT` pode definir sua raiz (padrão: pasta do manifest).
Essa configuração inicial escolhe um manifest por processo; a função de serviço
aceita store por empresa. O SaaS deverá escolher o store pela identidade
autenticada antes de atender várias empresas no mesmo processo. Manifest de
outra empresa é recusado, inclusive antes do cálculo no endpoint novo.
Nenhum endpoint público serve os bytes das imagens nesta etapa.

Interfaces Python novas:

| Interface | Contrato |
| --- | --- |
| `finish_identity(value)` | Unicode NFC/strip/uppercase; ausente retorna None, sem alias de cor |
| `model_identity(inputs, finish)` | chave de topologia e basename exato; campos do request normalizados; não calcula medidas |
| `ImageSelector` / `key()` | `kind`, `model_key`, `code`, `finish_key`; JSON canônico da identidade |
| `StoredProductionImage` | selector, relative_path, sha256, media_type, width_px, height_px, finish_policy |
| `ProductionImageManifest` | schema_version, company_id, source_workbook_sha256, entries; identidades únicas |
| `LayoutImage` | selector, status, relative_path, sha256, media_type, width_px, height_px, finish_policy; sem caminho absoluto |
| `image_metadata(bytes)` | valida raster e retorna media_type/largura/altura |
| `ProductionImageStore(root, manifest)` | raiz privada configurada no servidor, vinculada a uma empresa |
| `read_verified(entry)` | lê bytes após validar contenção, hash, formato e dimensões |
| `resolve(selector, company_id)` | VERIFIED/MISSING_ASSET/INVALID_ASSET; rejeita empresa divergente |
| `import_legacy_images(...)` | copia somente vínculos explícitos; retorna manifest e identidades ausentes; destino no repo exige `.private` |
| `legacy_anchor(family, line, inputs)` | retorna planilha, linha e label, ou linha/label desconhecidos; sem alterar dados técnicos |
| `LayoutItemLabel` | item_id e label |
| `ProductionLayoutContext` | company_id, client_code/name, work_code/name, item_labels |
| `ProductionLayoutRequest` | production_order e context |
| `ProductionItemHeader` | client_code/name, work_code/name, item_id/label, width_mm, height_mm, quantity |
| `LayoutFinding` | code, item_id, field, message, engine_position opcional |
| `ProductionLayoutRow` | print_position, engine_position, legacy_sheet/row, utilization_label, technical, profile_image |
| `ProductionLayoutBlock` | position, kind, columns, rows, repeat_columns_on_continuation, allow_continuation |
| `ProductionItemPagePlan` | item_id, position, page_format/orientation, regions, header_columns, header, model_description, finish_key, model_key, model_image, frame_section, leaf_section, blocks, ordering_status, findings |
| `ProductionLayoutDocument` | schema_version, company_id, order_id, ordering_version, technical_snapshot_sha256, header_snapshot_json, asset_manifest_sha256, pages, layout_sha256, audit_status |
| `build_production_layout(document, context, image_store=None)` | apresenta snapshot salvo sem recalcular; não muda/remover linhas |
| `prepare_production_layout(request, image_store=None)` | valida empresa, usa serviço existente de OP e monta o plano |
| `preview_production_layout(...)` | handler HTTP documentado no OpenAPI |
| `workbook_order(path)` / `reference_order(pdf_dir, order)` | extraem evidências técnicas sanitizadas, verificando hash da planilha |
| `technical_pdf_rows(text, allowed_labels)` | exporta somente utilizações/códigos de catálogo reconhecidos |
| `compare_layout_case(...)` / `build_report(image_store=None)` | compara ordem relativa/identidades; enumera adições, ausências e códigos divergentes |

Os scripts `audit_op_layout_sources.py`, `import_op_images.py` e
`compare_op_layout.py` documentam seus argumentos em `--help`. Os schemas completos
também estão no OpenAPI. O servidor não recebe paths de origem no corpo HTTP.

## Reprodução e recursos privados para outro ambiente

São necessários, fora do Git: a planilha do SHA oficial, os três PDFs para
reextrair a evidência e as pastas originais CROQUIS/CROQUIS_PERFIS. Para usar o
preview não é necessário colocar os PDFs/Excel no servidor: basta importar os
originais indicados no inventário e montar o volume privado com manifest.

```powershell
python -m pip install -r tools/requirements-op-audit.txt
python tools/audit_op_layout_sources.py --workbook "$env:OP_WORKBOOK" --pdf-dir "$env:OP_REFERENCE_PDFS" --order-output api/app/data/op_legacy_order_v1.json --reference-output api/tests/fixtures/op_layout_reference_v1.json
python tools/import_op_images.py --workbook "$env:OP_WORKBOOK" --legacy-root "$env:OP_LEGACY_LIBRARY" --inputs api/tests/fixtures/op_reference_inputs.json --company-id 00000000-0000-0000-0000-000000000001 --output-root .private/op-b1/images --include-fixo-reference
$env:OP_IMAGE_MANIFEST = ".private/op-b1/images/manifest.json"
python tools/compare_op_layout.py --manifest .private/op-b1/images/manifest.json --output .private/op-b1/verified-layout-comparison.json
python tools/compare_op_layout.py --output docs/audits/op_b1/layout_comparison.json
```

As variáveis de origem devem ser configuradas localmente; não são persistidas
no código ou nos relatórios públicos. `.private/`, PDFs, XLSM e RAR estão
ignorados pelo Git, com teste automatizado. O manifest e os 25 vínculos/bytes
importados ficam somente em `.private/op-b1/images`. Dados reais de cliente/
obra não foram incorporados aos fixtures, documentos ou commit. Os pequenos
rasters criados pelos testes servem apenas para validar formato/integridade em
diretórios temporários: não são croquis, não entram no produto ou no Git.

## Pendências para a próxima etapa

Auditoria independente desta entrega; inputs originais completos dos 12 casos;
confirmação das unidades fracionárias; revisão de consumo agregado; validação
visual dos JPGs contra as imagens dos PDFs; rótulos/continuação de grades
dinâmicas; OP real de FX (inclusive label legado FX!A27); diagramação e
paginação A4; autorização/autenticação e origem definitiva de cliente/obra;
armazenamento e entrega privada dos assets no ambiente publicado. A presença de
imagens e âncoras não resolve essas pendências nem autoriza fabricar.

## Verificações executadas e arquivos

Execução local em 05/11/2026, Python 3.13.17:

| Suíte | Resultado real |
| --- | --- |
| Engine ativa completa | 381 testes passaram |
| API completa | 154 executados: 153 passaram, um skip |
| Novos testes B1, incluídos na API | 46 executados: 45 passaram, um skip |
| Comparação A preservada | 129 campos da fixture iguais; suplementos mantêm duas divergências |
| Sequência B1 | 12/12 ordens relativas coincidem; 355/355 linhas preservadas |
| Importação real privada | 25 vínculos relidos/verificados; 36 slots principais resolvidos |

O skip local é a criação de symlink, sem privilégio no Windows. A CI Linux
executa a verificação de escape por symlink na leitura e na importação. Não foi
contado como teste aprovado localmente. O aviso existente de depreciação de
httpx/TestClient não foi suprimido. YAML, AST Python e `git diff --check` passaram.
A CI também reproduz o relatório B1 e compara-o com o arquivo versionado,
além das regressões existentes de Web/navegador/launcher.

Comandos das regressões (raiz do repositório, venv ativo):

```powershell
python -m pip install -r api/requirements-dev.txt
python -m unittest discover -s "engine/Software_Esquadrias_Starter + Versões/Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI/tests"
python -m unittest discover -s api/tests
python tools/compare_op_golden.py
python tools/compare_op_layout.py
```

Arquivos modificados:

- `.github/workflows/ci-software-esquadrias.yml`: reprodução da evidência B1.
- `.gitignore`: proteção da importação e das fontes privadas.
- `api/README.md`: endpoint e documentação B1.
- `api/app/main.py`: endpoint JSON e configuração privada do store.
- `api/requirements.txt`: Pillow para verificar os bytes originais.
- `docs/ORDEM_PRODUCAO_V1.md`: estado autorizado e referência B1.

Arquivos criados:

- `api/app/data/op_legacy_order_v1.json`: âncoras técnicas sanitizadas.
- `api/app/production_images.py`: identidades, manifest, importação e leitura verificada.
- `api/app/production_layout.py`: schemas e montagem de cabeçalhos/blocos.
- `api/app/production_ordering.py`: associação de roles à sequência da fonte.
- `api/tests/fixtures/op_layout_reference_v1.json`: evidência de sequência das 12 páginas.
- `api/tests/test_production_layout.py`: 46 testes B1, incluindo 12 casos individuais.
- `docs/OP_FASE_B1.md`: este relatório técnico.
- `docs/audits/op_b1/image_inventory.json`: inventário público sem bytes privados.
- `docs/audits/op_b1/layout_comparison.json`: relatório reproduzível por caso/linha.
- `tools/audit_op_layout_sources.py`: leitura sanitizada de Excel/PDF.
- `tools/compare_op_layout.py`: comparação de ordem, identidades e diferenças.
- `tools/import_op_images.py`: CLI de importação privada dos originais.
- `tools/requirements-op-audit.txt`: dependências opcionais da inspeção privada.
