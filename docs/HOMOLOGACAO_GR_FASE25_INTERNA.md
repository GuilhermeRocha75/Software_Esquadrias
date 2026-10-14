# Homologação interna GR — Fase 25

## Objetivo

Validar a migração GR sem depender do Microsoft Excel instalado ou ativado.
O arquivo oficial permanece somente leitura. O cálculo é feito diretamente a
partir das fórmulas OpenXML da aba `GR`.

Fonte oficial:

- SHA-256: `96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`
- 1.684 registros GR na `ORCS`
- 162 combinações técnicas inventariadas

## Componentes

- `tools/gr_formula_oracle.py`: interpreta as fórmulas GR sem Office.
- `tools/compare_gr_formula_engine.py`: compara o resultado legado com a
  Engine `GR_ENGINE_0.25.0`.
- `tests/test_gr_formula_oracle.py`: regressão do avaliador e da matriz de
  diferenças homologadas.

O avaliador suporta exatamente as funções presentes na aba GR: `IF`, `AND`,
`OR`, `VLOOKUP`, `SUM` e `LEFT`, além de referências, intervalos, operadores
aritméticos, comparações e concatenação.

## Execução

Na raiz do projeto:

```powershell
python .\tools\compare_gr_formula_engine.py `
  "C:\caminho\SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm" `
  --output "$HOME\gr-parity-report.json"
```

O comando termina com código `0` somente quando:

1. o hash da planilha é o oficial;
2. o total recalculado pelas fórmulas permanece no baseline aprovado;
3. o total da Engine permanece no baseline aprovado;
4. toda diferença possui correção física documentada.

Para extrair somente o resultado das fórmulas:

```powershell
python .\tools\gr_formula_oracle.py `
  "C:\caminho\SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm" `
  --rows 270 11480 14891 15295 16527 18132 18545 `
  --output "$HOME\gr-formula-oracle.json"
```

## Política de paridade

`EXACT_MATCH` significa igualdade numérica. `DOCUMENTED_CORRECTION` significa
que os dois lados permaneceram nos valores congelados e o delta corresponde a
uma correção física já identificada. Qualquer outra mudança é `FAIL`.

Não é correto exigir igualdade literal nos casos em que o XLSM omite materiais
físicos ou mantém uma geometria comprovadamente incorreta. Isso reintroduziria
na aplicação os erros que a migração decidiu corrigir.

## Privacidade

O oráculo carrega da `ORCS` somente as colunas técnicas `D:I` e `K:AK`.
Campos de cliente, item e local não são carregados nem emitidos no relatório.

## Limite

O teste substitui o recálculo nativo do Excel para o escopo GR coberto pelas
fórmulas atuais. Se a aba GR passar a usar nova função, vínculo externo, macro
ou nome dinâmico, o avaliador falhará explicitamente até que o novo contrato
seja revisado.
