# Validação técnica do Modelo Fixo

Fonte: aba FX do XLSM oficial, SHA-256
`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`.
Branch: `feature/fixo-engine-v1`. Data: 16/10/2026.

## Resultado

Validação técnica aprovada no escopo das fórmulas FX e do catálogo existente.
Não houve alteração de fórmulas, preços ou substituição automática de vidros.

| Verificação | Resultado |
| --- | ---: |
| Registros históricos examinados | 1.612 |
| Registros válidos, com paridade de toda a BOM e dos totais | 1.538 |
| Fórmulas conferidas contra o cache da fonte | 148, sem divergências |
| Combinações adicionais examinadas | 2.824 |
| Combinações adicionais válidas com paridade | 2.752 |
| Geometrias inválidas adicionais recusadas | 72 |
| Vidros do catálogo cobertos | 61 |
| Divergências nos cálculos válidos | 0 |
| Maior delta absoluto por ponto flutuante | 3,64 × 10⁻¹² |

A matriz adicional exercita todos os vidros com V=0..7 e H=0..4, além de
dimensões fracionárias, quatro combinações de acabamentos, quantidades 1/2/7 e
geometrias próximas do limite do reforço. O oráculo executa fórmulas lidas do
arquivo original e não consulta resultados da Engine para calcular os esperados.

As exceções históricas foram revisadas e permanecem rejeitadas:

- 69 registros utilizam 18 descrições ausentes da LISTAVIDROS atual: o XLSM
  retorna #N/A e a Engine recusa o vidro sem atribuir preço substituto.
- 4 registros estão sem vidro informado: o XLSM retorna #VALUE! e a Engine
  recusa a entrada.
- A linha ORCS 8152 está sem largura e altura; a Engine recusa a geometria.

Essas 74 linhas são dados inválidos da fonte, não divergências nos 1.538
registros válidos. O relatório identifica cada descrição e suas linhas.
Reutilizá-las como novos orçamentos exige corrigir os dados de origem.

## Correções encontradas na validação

1. Dimensões finitas extremamente grandes podiam gerar infinito nos cálculos
   derivados e HTTP 500 na serialização. A Engine agora retorna erro de
   validação, convertido em HTTP 422, sem alterar o domínio de cálculos válidos.
2. A tabela exibia “Calculado” mesmo quando o pedido era recusado. Agora mostra
   “Não calculado” até haver um resultado válido para o pedido corrente.
3. Respostas recebidas fora de ordem podiam sobrescrever uma edição mais nova.
   Cada requisição é vinculada à versão do cálculo; resultados antigos são
   ignorados. Remover todos os itens também limpa o erro e o estado de cálculo.

## Regressão e interface

Validação local: **365 testes Engine, 75 API, 8 testes unitários Web, build de
produção e 8 testes de navegador aprovados**. Os testes anteriores de CR, MX e
GR continuam aprovados. O fluxo de navegador utiliza API real pelo proxy do Vite,
sem simular preços ou resultados de engenharia.

O navegador verifica quatro casos esperados diretamente da planilha, o número
de vidros no pedido, custo técnico, BOM e plano de corte; inclusão, edição,
persistência após recarregar e remoção; recuperação de erro 422 sem derrubar o
indicador de API; resposta antiga chegando depois da nova; inclusão em viewport
de celular de 390×844. O layout do configurador foi inspecionado em imagens de
desktop e celular. O relato do usuário de que o iniciador local funciona foi
registrado como confirmação de inicialização, sem extrapolar para homologação
dos cálculos.

O CI instala Chromium e executa a mesma suíte de navegador. O teste existente
do inicializador Windows continua no workflow. A aprovação remota deve referir
o commit final publicado, não apenas a contagem local.

## Casos para conferência funcional

Medidas em mm; custo técnico exclui margem de venda e incremento de compra de
barras. Vidros/pedido inclui a quantidade de produtos.

| Caso | L×A | V / H | Vidro | Produtos | Medida de cada vidro | Vidros/pedido | Custo técnico/pedido |
| --- | --- | --- | --- | ---: | --- | ---: | ---: |
| Simples | 1200×1000 | 0 / 0 | 04mm FLOAT INCOLOR | 1 | 1112×912 | 1 | R$ 422,02 |
| Grade | 2000×2200 | 2 / 3 | 08mm TEMPERADO INCOLOR | 2 | 608×495 | 24 | R$ 3.753,08 |
| Histórico 14 | 1560×2200 | 0 / 0 | 06mm FLOAT INCOLOR | 3 | 1472×2112 | 3 | R$ 2.836,48 |
| Vidro duplo | 3400×1800 | 3 / 1 | 20mm DUPLO FLOAT INCOLOR (4/10/6) | 1 | 795×834 | 8 | R$ 2.762,77 |

Todos usam GUARNIÇÃO DE 70MM interna e BARRA CHATA DE 30MM externa.

## Reprodução

Na raiz, com o Python do ambiente do projeto:

```powershell
python tools/validate_fixo.py "CAMINHO_DA_PLANILHA.xlsm" --output "$HOME\fixo-validacao.json"
```

O relatório técnico versionado fica em `test_cases/fixo_validation_v0_1.json`
dentro da Engine. A fonte permanece somente para leitura. Não inclui dados de
clientes ou a planilha completa.

Para o navegador, após instalar as dependências Python e executar `npm ci` em
`web/`:

```powershell
npx playwright install chromium
npm run test:e2e
```

Se o comando `python` não apontar ao ambiente virtual, defina `E2E_PYTHON` com
o caminho do executável. O teste inicia os serviços ou reutiliza os existentes
localmente; no CI exige serviços próprios.

## Gate

`PENDING_HOMOLOGATION`, `main_ready: false`.

O código e as evidências estão preparados para revisão funcional dos casos e
aceite do tratamento dos dados inválidos. Não houve merge na main nem alteração
na hospedagem. VPS e publicação externa permanecem adiados por decisão do usuário.
