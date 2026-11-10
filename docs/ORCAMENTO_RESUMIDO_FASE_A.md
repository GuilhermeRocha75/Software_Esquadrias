# Orçamento resumido — referência do Excel

Fonte: SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm, aba ORC IMP RES. As referências abaixo descrevem o arquivo original e permitem conferir a implementação sem publicar registros comerciais.

| Célula | Regra do Excel |
| --- | --- |
| J16:J70 | Se E contém quantidade, calcular largura C × altura D em mm × quantidade / 1.000.000. Com E vazia, retornar texto vazio. |
| D72 — Esquadrias | Somar G16:G66. |
| J72 | Somar áreas J16:J70. |
| K72 | Somar quantidades E16:E70. |
| D73 — Instalação | J73 × área total + K73 × quantidade total + L73. |
| D74 — Total | D72 + D73. |

O modelo soma os valores monetários até a linha 66, enquanto área e quantidade vão até a linha 70. A inspeção das fórmulas confirma a diferença. A investigação do VBA deve verificar quais linhas o fluxo de impressão realmente preenche.

## Caso de conferência sintético

Na linha 16, usar largura 1200 mm, altura 1500 mm, quantidade 2 e valor de linha G16 igual a 800. Deixar as demais linhas vazias. Com J73 = 100, K73 = 25 e L73 = 50, esperar área de 3,6 m², 2 unidades, instalação de 460 e total de 1260. Os valores são entradas de teste. A formação de G16 a partir do custo e da margem ainda exige rastrear o VBA.

## Origem dos itens

Na aba ORCS, D:F correspondem a largura, altura e quantidade. AL:AO correspondem a margem, código, modelo completo e custo. Examinar as rotinas que transferem esses dados às abas ORC IMP e ORC IMP RES para identificar cálculo de preço, arredondamento e substituição manual.
