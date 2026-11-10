# Fase B2 — geração e validação de PDF de conferência

Implementação para auditoria na branch `feature/ordem-producao-v1`, sobre
`0300810264610b21d58e0748b0fe469fb27f06c4`. A base B1 foi aceita com pendências
pelo proprietário. Esta entrega não conclui nem homologa a Ordem de Produção,
não libera fabricação e não faz merge na main.

## Funcionalidades e limites

`api/app/production_pdf.py` renderiza A4 retrato a partir do snapshot imutável
`ProductionLayoutDocument` da B1, usando ReportLab e fontes Vera incorporadas.
O renderer não chama a Engine nem recalcula cortes, quantidades, consumo ou
geometria. A entrada HTTP monta o contrato B1 pelos serviços já existentes.
Nenhuma fórmula ou arquivo de engenharia foi modificado.

Cabeçalho inclui cliente, obra, item, largura, altura e quantidade. Croqui,
seções e perfis usam os assets reais importados pela B1, resolvidos por empresa,
código, identidade do modelo e acabamento, com hash verificado. Manifest de
outra empresa ou diferente do snapshot é recusado. Arquivo indisponível gera
pendência e texto de ausência, sem imagem substituta. Não há leitura de paths
fornecidos pelo cliente nem download de imagens externas.

As 355 linhas calculadas para os 12 casos aparecem em sequência B1. Medidas
finais e de corte são distintas; vidros/telas exibem largura e altura. A tabela
mostra quantidades totais; anexo preserva quantidade por esquadria quando
diferente, fator BOM e unidades físicas pendentes. Valores são formatados com
`Decimal(str(valor))`, sem arredondamento; inclusive a precisão bruta de floats
da Engine permanece visível. Unidades não confirmadas não viram contagem física.

Paginação automática repete identificação e colunas, continua linhas longas
e repete seu código nas continuações. Cada item começa em nova página. Anexos
reúnem bloqueios e divergências por item, incluindo dados originais das linhas
ausentes. Essas linhas de referência não são inventadas na BOM calculada.
Códigos longos também aparecem completos no anexo. Textos excessivos no
cabeçalho e glifos sem suporte são recusados explicitamente em vez de sumirem.
Paths Windows/UNC/file e sentinela legada isolada `A` são ocultados na impressão
e sinalizados. Código `0`, quando presente no contrato, continua sendo impresso.

O layout mantém croqui, barras pretas, grupos e colunas do legado. Coordenadas
de caixas de imagens foram medidas nos 12 PDFs e estão no template sanitizado
`op_pdf_geometry_v1.json`, com hashes das fontes. Trata-se de geometria gráfica,
não de dimensões de fabricação. Há diferenças de fontes/espaçamento, títulos,
seções adicionais no topo, unidades, obra e anexos. Não se afirma identidade
visual exata. [Conferência visual por caso](audits/op_b2/visual_review.md).

## Contratos, API e preparação Web

- `POST /api/v1/production-orders/pdf-readiness`: recebe `ProductionLayoutRequest`
  da B1 e retorna `review_allowed`, `fabrication_allowed: false`, hash e bloqueios.
- `POST /api/v1/production-orders/pdf`: recebe
  `{"layout_request": <requisição B1>, "purpose": "REVIEW"}`. Retorna PDF privado,
  `Cache-Control: private, no-store`, nome seguro baseado em hash, `nosniff` e
  headers expostos via CORS: `X-OP-Mode`, `X-OP-Fabrication-Allowed`,
  `X-OP-Blocking-Count`, `X-OP-Pages`, `X-OP-Snapshot-SHA256` e Content-Disposition.
- `purpose: "PRODUCTION"` retorna HTTP 409 / `FABRICATION_BLOCKED`. Há sempre o
  bloqueio `INDEPENDENT_DOCUMENT_AUDIT_PENDING`, mesmo com assets, contexto e
  inputs completos. O cliente não pode sobrescrever `fabrication_allowed`.
- Todas as páginas trazem **CONFERÊNCIA — NÃO FABRICAR**. Nenhuma opção remove
  a marca. O renderer não persiste arquivo nem cria rota pública de assets.
- `web/src/productionOrderPdf.js` prepara o consumo futuro: solicita só REVIEW,
  valida MIME, headers, páginas, bloqueios, hash e assinatura `%PDF-`, respeita
  cancelamento e devolve Blob. Não habilita botão nem altera a interface atual.

`ProductionPdfResult` contém bytes e `ProductionPdfAudit`, com hashes do layout,
PDF, notas, identificação textual e template, número de páginas, rastros de cada
célula/linha e posição das imagens. `PdfModelHeading` valida item e identidade
contra o snapshot. Notas e identificação são sidecars com hashes próprios;
reimpressão determinística exige o mesmo snapshot, sidecars, bytes dos assets e
versões de dependências. Não há promessa de bytes iguais entre versões futuras
do ReportLab. `OP_PDF_B2_0.1.0` identifica esta apresentação.

## PDFs privados e integridade

Entrega em `.private/op-b2/review/`, ignorada pelo Git:

- `OP-GOLDEN-01.pdf` a `OP-GOLDEN-12.pdf`: oito CR, três MAXIM_AR e um GR.
- `FX-PROPRIO.pdf`: caso próprio 1200 × 1000, quantidade 1, sem referência FX.
- `OP-REFERENCIAS-12.pdf`: reunião dos 12 casos, **26 páginas**.
- `OP-B2-CONFERENCIA.zip`: os 13 PDFs individuais e o PDF reunido, sem originais.
- `audits/*.json`: rastros detalhados dos PDFs; `visual/*.png`: pares privados.

Os casos 06 e 12 têm três páginas; os demais têm duas. O caso 06 usa uma página
de tabela e duas de anexo; o 12 usa duas de tabela e uma de anexo. O FX tem duas.
Total dos individuais: 28 páginas. A paginação adicional é deliberada para
preservar dados e pendências, sem alegar equivalência a uma página original.

O inspetor `tools/inspect_op_pdf.py` é independente do renderer e não importa a
Engine. Lê o PDF efetivo com pypdf/PyMuPDF: verifica SHA, A4, páginas, marca em
todas as páginas, texto fora dos limites, ausência de paths, e cada célula pelo
texto efetivamente decodificado dentro de sua caixa. Verifica os bytes e pixels
dos streams de imagens e suas posições efetivas. Para os 12 casos: **355 linhas,
1.853 células e 84 posições de imagens verificadas**, sem erro de integridade.
FX: **13 linhas, 74 células, quatro posições**, sem erro. Não houve perda de
linha, dimensão ou quantidade do contrato B1. Isso não equivale a provar que a
BOM B1 já contém todas as linhas originais.

As imagens privadas reais estavam disponíveis. Foram usadas as 25 associações
de assets da B1; os três PDFs originais são conferidos por seus hashes. Dados
de cliente dos candidatos são anonimizados. Referências, workbook, imagens,
PDFs e rasters ficam fora do repositório público. Só contratos, números técnicos
sanitizados, geometria de caixas, hashes e relatório sem cabeçalhos privados
entram no Git. Nenhum PDF original ou imagem original foi publicado.

## Divergências por item

O [relatório estruturado completo](audits/op_b2/pdf_review_report.json) contém
códigos, posições, dimensões, quantidades, valores fonte/Engine, classificações
e inputs faltantes de cada item. As contagens B1 permanecem **13 linhas
adicionais, 34 ausências e 26 diferenças de código**, totalizando 73 ocorrências.
São 342 linhas comuns: 376 originais menos 34 ausentes; mais 13 adicionais
resultam nas 355 linhas calculadas, todas preservadas.

| Caso | Família | Adicionais | Ausências | Códigos | Numéricos iguais / divergentes / precisão |
| --- | --- | ---: | ---: | ---: | --- |
| 01 | CR | 0 | 4 | 3 | 63 / 2 / 0 |
| 02 | CR | 0 | 4 | 3 | 63 / 2 / 0 |
| 03 | GR | 3 | 1 | 1 | 52 / 1 / 1 |
| 04 | CR | 0 | 4 | 3 | 48 / 2 / 0 |
| 05 | CR | 0 | 4 | 3 | 76 / 3 / 0 |
| 06 | CR | 0 | 4 | 4 | 48 / 2 / 0 |
| 07 | CR | 0 | 4 | 3 | 48 / 2 / 0 |
| 08 | MAXIM_AR | 3 | 0 | 0 | 51 / 0 / 0 |
| 09 | CR | 0 | 4 | 3 | 48 / 2 / 0 |
| 10 | MAXIM_AR | 3 | 0 | 0 | 51 / 0 / 0 |
| 11 | MAXIM_AR | 3 | 0 | 0 | 51 / 0 / 0 |
| 12 | CR | 1 | 5 | 3 | 71 / 11 / 0 |

As 73 ocorrências B1 foram classificadas conservadoramente:

- 32 ausências de arremates CR associadas a inputs reconstruídos sem acabamento;
- 25 diferenças ligadas a opções de vidro/ferragem não confirmadas;
- uma ausência GR possivelmente ligada a variante legada/engenharia;
- 12 borrachas adicionais (três GR e três em cada MX), regras existentes não
  demonstradas pela impressão original;
- duas diferenças do kit com modo de persiana reconstruído não confirmado;
- uma anomalia legada de identificação (linha com código 0).

Essas classificações são hipóteses de causa, não explicações comprovadas.
Imprimir croqui do acabamento correto não corrige o input técnico incompleto.

A nova fixture numérica transcreve apenas as 376 linhas técnicas dos PDFs,
sem clientes. Sobre as linhas comuns, foram comparados **698 campos: 670 iguais,
27 divergentes e uma diferença de precisão impressa**. As 18 linhas de
consumíveis em metros por pedido ficam separadas como revisão de representação
de unidade, pois B1 fornece mm/esquadria e conjuntos. Nenhuma conversão ou
fórmula de consumo foi criada na camada PDF para forçar coincidência.

Achados numéricos além da fixture parcial A/B1:

- **PAR2 em oito CR**: diferenças de quantidade 0,8 por esquadria (1,6 no item
  06 com quantidade 2). Exemplos: item 01, 83,424 na fonte × 84,224 na Engine;
  item 06, 133,984 × 135,584. Causa ainda aberta: variante legada ou engenharia;
  não é tratada como defeito de PDF nem ajustada na apresentação.
- **Ferragens**: oito quantidades de contra-fecho CR e uma de parafusos GR
  divergem; hipótese de opções reconstruídas incompletas. GR: PAR1 36 × 28.
- **OP3 / item 12**: eixo original 950 mm × 1940 mm na reconstrução de eixo
  compartilhado (final e corte), e seis quantidades do kit 2 × 1. É necessária
  confirmação do modo original de persiana/eixos; hipótese não encerrada.
- **Duas persianas já conhecidas**: item 05, tala 40,25 × 41; item 12, 59 × 60.
  A Engine mantém sua regra física existente. O input original e a convenção
  de contagem precisam de validação; não houve arredondamento pelo PDF.
- **Painel GR**: 12,8357143 impresso × 12,835714285714285 na Engine. Classificado
  como precisão impressa (tolerância de comparação 0,000001, sem alterar valor),
  com unidade física fracionária ainda pendente.

A fixture parcial anterior continua com seus 129 campos de referência
coincidentes e duas divergências de tala no suplemento. Ela não cobria PAR2
nem todas as linhas do kit. A nova auditoria não promove amostra parcial a
equivalência integral. Nenhum dos 12 candidatos é declarado equivalente ao
original para fabricação. FX não tem documento original e seu rótulo B1
`Vidros (Band. Sup.)` em caso simples também precisa de revisão de apresentação.

## Testes e reprodução

Resultados locais, Windows:

| Verificação | Resultado |
| --- | --- |
| Engine completa | 381 aprovados |
| API completa, incluindo B2 | 192 executados: 191 aprovados, um ignorado por symlink Windows |
| Subconjunto PDF B2 | 38 aprovados, incluídos na contagem da API |
| Web unitários | 12 aprovados |
| Web build | concluído |
| Web navegador (Chromium, API real) | nove aprovados |
| PDFs privados reais | 13 gerados, integridade aprovada; 12 comparados com referências |

Testes B2 cobrem quatro famílias, 12 referências, todas as medidas/quantidades
do contrato, snapshot determinístico sem Engine, paginação com mais de 80
linhas, linha de 2.400 palavras continuada, imagens/posições, fonte sem glifo,
fracionários, fator BOM, códigos longos/0, ordem mista, hashes/empresa, assets
ausentes, dados locais ocultados, detecção de PDF alterado e gates HTTP/Web.
Os rasters mínimos dos testes são criados em diretório temporário para testar
o mecanismo; não são assets de produto nem substituem imagens nos PDFs reais.

```powershell
.\.venv\Scripts\python.exe -m pip install -r api/requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s 'engine/Software_Esquadrias_Starter + Versões/Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI/tests'
.\.venv\Scripts\python.exe -m unittest discover -s api/tests
# Em web/: npm ci; npm test; npm run build; npx playwright install chromium
# E2E_PYTHON deve apontar ao Python da .venv no Windows; npm run test:e2e
.\.venv\Scripts\python.exe tools/generate_op_review_pdfs.py --manifest .private/op-b1/images/manifest.json --reference-dir <pasta-dos-tres-PDFs> --output-dir .private/op-b2/review --public-report docs/audits/op_b2/pdf_review_report.json
```

As extrações opcionais `audit_op_pdf_geometry.py` e `audit_op_pdf_numeric.py`
exigem os originais com hashes B1; geração normal usa os templates sanitizados.
Assets privados são configurados na API por `OP_IMAGE_MANIFEST` e
`OP_IMAGE_STORAGE_ROOT`, conforme B1. CI executa regressões sem dados privados.
O gerador recusa saída dentro do repositório fora de `.private/`.

Inicialmente faltavam Playwright/Chromium no ambiente local: dependências
foram reinstaladas por `npm ci` e o navegador foi instalado para executar os
testes existentes. A reinstalação apontou dois avisos de severidade alta no
lockfile Web preexistente (`vite` e `source-map-js`, dependências de tooling).
`npm audit` retorna 1; dependências Web não foram alteradas nesta fase.
Tratamento dessa dívida deve ser acompanhado separadamente, sem confundir
aprovação das regressões funcionais com auditoria de dependências.

## Arquivos desta entrega

- API: `production_pdf.py`, template `data/op_pdf_geometry_v1.json`, rotas e
  CORS em `main.py`, dependência ReportLab e dependências de teste pypdf/PyMuPDF.
- Testes: `test_production_pdf.py` e fixture sanitizada
  `op_pdf_numeric_reference_v1.json`.
- Ferramentas: `generate_op_review_pdfs.py`, `inspect_op_pdf.py`,
  `audit_op_pdf_geometry.py`, `audit_op_pdf_numeric.py`,
  `compare_op_pdf_numeric.py`.
- Web: helper `src/productionOrderPdf.js` e testes correspondentes; sem UI nova.
- Documentação: este relatório, especificação V1, READMEs API/Web,
  `audits/op_b2/pdf_review_report.json` e `audits/op_b2/visual_review.md`.

## Pendências para próxima decisão

A infraestrutura está pronta para auditoria do PDF e futura prévia Web. A
emissão de ordens para fábrica continua bloqueada. É necessário confirmar os
inputs originais de acabamento/vidro/ferragens/persianas, investigar PAR2,
validar linhas ausentes/adicionais e unidades fracionárias/consumo, revisar o
rótulo FX, conferir visualmente os PDFs com o usuário e obter auditoria
independente. Persistência, autorização multiempresa e workflow de liberação
de fabricação não foram introduzidos nesta entrega. `company_id` e verificação
dos assets preservam o isolamento contratual existente, sem substituir futura
autenticação. Nenhuma dessas pendências é encerrada por testes de integridade.
