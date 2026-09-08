# Diagnóstico do plano de compra enviado — v0.3.1

## Resumo do CSV

- 19 materiais em barra
- consumo: 335,244 m
- compra: 401,200 m
- sobra: 65,956 m
- aproveitamento global: 83,56%
- custo pelo consumo: R$ 7.445,40
- custo de compra: R$ 9.445,07

## Comparação com PPED_P do Excel

Diferenças de consumo observadas:

| Código | Excel (m) | Tester v0.3 (m) | Interpretação |
|---|---:|---:|---|
| PR8852 | 20,040 | 18,040 | entradas de dimensões não idênticas |
| PR4536 | 9,608 | 11,608 | entradas de altura não idênticas |
| AL16 | 9,584 | 5,584 | entradas de largura não idênticas |
| AC7012 | 38,240 / 16 cortes | 34,100 / 15 cortes | aplicação JANELA/PORTA diferente |
| AC3004 | 36,960 / 16 cortes | 32,900 / 15 cortes | aplicação JANELA/PORTA diferente |
| RAG - PR8852 | 19,168 | 17,168 | entradas de dimensões não idênticas |

A combinação dos números indica que as duas esquadrias PRIME foram lançadas na v0.3 como
1500 × 3000, enquanto no Excel uma delas é 3500 × 2000.

Também há evidência de que um DESIGN foi informado como aplicação PORTA na v0.3,
enquanto no Excel os dois DESIGN do teste estão como aplicação JANELA.

## Alertas

### DT-CR-003
Informação de compatibilidade. Hoje PRIME e DESIGN possuem 8 mm nesse parâmetro,
portanto o aviso não altera o resultado numérico atual.

### LEGACY-PEDP-DE5013
Inconsistência real do legado no pedido histórico consolidado entre itens.
Quatro cortes de 1902 mm somam 7608 mm e não cabem em uma barra de 5900 mm.
A Engine mantém 2 barras e sinaliza a divergência somente nessa assinatura.
No caso unitário DESIGN 2000 × 2000 de 4 folhas, o Excel também retorna 2 barras.
