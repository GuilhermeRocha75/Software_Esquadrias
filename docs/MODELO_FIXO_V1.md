# Modelo Fixo — FX_ENGINE_0.1.0

Branch: `feature/fixo-engine-v1`, iniciada na `main` em
`30d57318e0885ac04145b44b77d0e7d306d586b3` (GR finalizada).

## Fonte e método

Fonte: `SOFTBETA_ PERFIL PRE DELL AMANDA(1).xlsm`, aba `FX`.
SHA-256: `96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`.

Método repetido do GR: engenharia reversa, casos históricos, oráculo de fórmulas
independente, golden cases, implementação, regressão, revisão e homologação.
O arquivo original é somente lido como OpenXML. Não há execução de macros nem
dependência de Office no motor. Nenhuma fórmula técnica foi acrescentada à API
ou à interface. Não houve alteração de regra física em relação à FX.

## Contrato e fórmulas

`V = vertical_transoms`, `H = horizontal_transoms`, dimensões em milímetros.

| Origem | Entrada ou regra migrada |
| --- | --- |
| FX!D2:E2:F2 | Largura, altura e quantidade do pedido |
| FX!K2 / K3:K4 | Vidro com lookup exato, sem diferenciar maiúsculas; espessura nos dois primeiros caracteres |
| FX!S2:T2 | Acabamentos interno/externo do catálogo |
| FX!AJ2:AK2 | Quantidades inteiras de travessas verticais e horizontais |
| FX!8:9 | Marco DE6058, duas larguras e duas alturas; corte = medida externa + 5 |
| FX!10 | H × (V+1) travessas horizontais; corte = (largura − 80 − V×36)/(V+1) |
| FX!11 | V travessas verticais inteiras; corte = altura − 80 |
| FX!12:13 | Baguetes de cada vão; largura = (largura − 80 − V×36)/(V+1), altura = (altura − 80 − H×36)/(H+1) |
| FX!14:17 / PFAB!B14:B15 | Dois cortes por eixo; interno +140, externo +60, independentemente do perfil selecionado |
| FX!20:21 | Reforços do marco RAG-DE6058: corte = dimensão externa − 116 + 5 |
| FX!22:23 | Reforços de travessa RAG-DE6072: mesmos comprimentos/quantidades das travessas |
| FX!27 / PFAB!B12 | (V+1)×(H+1) vidros; medida de cada vão menos 8 em cada eixo |
| FX!30:31 | Dois calços por vidro e dois tapas deságue por unidade de produto |
| FX!I18/I24/I28/I32/I34/AO2 | Subtotais de perfis/reforços/vidros/acessórios e custo técnico unitário |

Baguetes em `FX!B12`: espessura <8 → BA3518; 8–11 → BA3218;
12–18 → BA2516; 19–21 → BA2018; 22–25 → BA1816; 26–30 → BA1216;
31–33 → BA1016; 34 → BA0716. Só são oferecidos os vidros existentes na
LISTAVIDROS. Não se inventam composições ou preços para os limites sem produto.

Os catálogos compartilhados existentes fornecem os preços. A comparação avalia
também código, preço unitário, quantidade unitária/pedido, comprimento de corte,
medidas do vidro e custo de **cada** linha da BOM, além dos subtotais e total.
Preços gravados como texto com vírgula e códigos numéricos são convertidos para
número e identificador textual, respectivamente, sem alterar seus valores.

O número de produtos não altera o custo unitário. O custo do pedido é multiplicado
pela quantidade. O plano de compra utiliza o otimizador existente, separando
custo por consumo e custo por aquisição. O endpoint FX permite configurar o
comprimento da barra e a perda de serra. Cortes acima da barra disponível são
recusados pelo plano de compra; o cálculo técnico continua disponível.

Não foram importados para FX os parafusos, vedações, persianas, telas, ferragens,
bandeiras ou regras de folha móvel dos outros modelos: a aba original não os
calcula. Campos antigos residuais de outras famílias na ORCS não alteram a FX.
Divisões personalizadas não existem nas fórmulas FX e não são oferecidas.

## Evidência de paridade

| Verificação | Resultado |
| --- | ---: |
| Registros ORCS identificados como FX | 1.612 |
| Registros válidos com paridade de toda a BOM e totais | 1.538 |
| Divergências entre Engine e fórmulas em registros válidos | 0 |
| Maior diferença absoluta de total, por ponto flutuante | 3,64 × 10⁻¹² |
| Erros #N/A da planilha, vidro ausente do catálogo | 69 |
| Erros #VALUE! da planilha, vidro não preenchido | 4 |
| Entrada com largura inválida (ORCS 8152) | 1 |
| Fórmulas FX recalculadas contra os valores salvos na fonte | 148, sem divergências |
| Casos históricos congelados por grade e espessura | 66 |

Os 74 casos problemáticos estão identificados individualmente em
`test_cases/fixo_coverage_v0_1.json`, com entradas técnicas e razão de rejeição.
O motor recusa esses dados, sem substituir automaticamente o vidro ou seu preço.
Para migrar tais orçamentos será necessário corrigir o cadastro de origem ou
definir explicitamente a composição/preço que faltam. Isso não constitui
divergência das 1.538 configurações válidas, mas impede declarar todo o histórico
como homologado.

O snapshot de fórmulas/catálogos e os golden cases são exclusivamente técnicos.
Não contêm planilha completa, clientes, códigos de cliente, locais ou dados
comerciais privados. Os testes também exercitam todos os vidros do catálogo em
quatro topologias de grade, limites de baguete, entradas inválidas, quantidade,
aquisição, barras configuráveis e pedidos mistos CR/MX/GR/FX.

## Integração

- `GET /api/v1/engine/fixo/options`
- `POST /api/v1/engine/fixo/calculate`
- `POST /api/v1/engine/fixo/purchase-plan`
- `POST /api/v1/purchase-plans/calculate-all`: itens `family: "FX"` ao lado de CR/MX/GR.
- Interface: botão lateral “Inserir Modelo Fixo”, inclusão, edição, remoção,
  persistência local e resultado no pedido, BOM e plano de compra.

Exemplo:

```json
{"family":"FX","width_mm":2000,"height_mm":2200,"quantity":2,
 "vertical_transoms":2,"horizontal_transoms":3,
 "glass_description":"08mm TEMPERADO INCOLOR",
 "internal_finish":"GUARNIÇÃO DE 70MM","external_finish":"BARRA CHATA DE 30MM"}
```

## Reproduzir a auditoria

Na raiz do repositório, com o ambiente Python do projeto:

```powershell
python tools/compare_fixo_formula_engine.py "CAMINHO_DA_PLANILHA.xlsm" --output "$HOME\fixo-parity-report.json"
```

O comando falha se houver qualquer divergência de paridade, aceitação inesperada
de erro da fonte ou diferença na checagem de fórmulas salvas. As exceções de
origem são relatadas separadamente; exit code 0 **não** significa homologação de
todos os registros nem autorização para merge.

As suítes Engine/API e os testes/build Web são executados no workflow
`ci-software-esquadrias.yml`, incluindo pushes desta branch. Os testes técnicos
rodam sem o XLSM privado a partir das evidências congeladas.

Validação ampliada em 16/10/2026: 365 testes Engine, 75 testes API, 8 testes
unitários Web, build de produção e 8 testes em navegador real aprovados.
Foram examinadas mais 2.824 combinações, sem divergências nos cálculos válidos.
Os fluxos de inclusão, edição, persistência, exclusão, erro, resposta fora de
ordem e uso em celular foram exercitados com a API real.
Veja [VALIDACAO_FIXO_V1.md](VALIDACAO_FIXO_V1.md) para os resultados, correções
de validação e casos de conferência funcional.

## Estado para merge

`PENDING_HOMOLOGATION`, `main_ready: false`.

Antes do merge: conferir o fluxo da interface com a equipe e homologar o
tratamento das 74 exceções de origem. Preservar os resultados de regressão e
validar o mesmo commit no CI. Não houve merge na `main` nesta entrega.
