# Diagnóstico dos testes reais — v0.3

## 1. O que estava diferente

A Engine v0.2 calculava o **consumo efetivo** de cada material:

`comprimento do corte × quantidade × preço por metro`

Isso é útil para engenharia e margem técnica, mas não representa o desembolso para comprar perfis.

O Excel possui uma segunda lógica na aba `PED_P`:

`quantidade de barras × 5,900 m × preço por metro`

O comprimento da barra está em `PFAB!B16 = 5900 mm`.

## 2. Como o Excel determina a quantidade de barras

O arquivo de teste contém `PPED_P`, com todos os cortes necessários ao pedido.

Ao reconstruir o agrupamento:

1. agrupar os cortes por código de perfil;
2. ordenar os cortes do maior para o menor;
3. colocar cada corte na primeira barra de 5900 mm em que ele couber;
4. abrir nova barra quando não couber em nenhuma existente.

Esse algoritmo é conhecido como **First Fit Decreasing (FFD)**.

Ele reproduziu 18 das 19 quantidades do `PED_P` do arquivo enviado.

## 3. Defeito detectado no legado em consolidação entre itens

`DE5013 — TAPA FOLHA PORTA DE CORRER`

No `PPED_P` existem:

- 4 cortes;
- cada corte = 1902 mm;
- total = 7608 mm.

Uma barra tem 5900 mm. Logo são fisicamente necessárias 2 barras.

O `PED_P` legado registra apenas 1 barra nesse pedido com os cortes provenientes
de mais de um item.

Controle negativo: um único item DESIGN 2000 × 2000 de 4 folhas também gera
4 cortes de 1902 mm, mas o Excel indica corretamente 2 barras. Portanto, não se
deve generalizar a divergência apenas por quantidade e comprimento dos cortes.

A v0.3 calcula 2 barras e emite o alerta `LEGACY-PEDP-DE5013`.

PED_P legado: **R$ 9.537,055**

Plano correto com a segunda barra DE5013:
**R$ 9.596,881**

Diferença: **R$ 59,826**.

## 4. Aplicação é independente do perfil da folha

O Excel possui:

- `H`: tipo de folha;
- `I`: aplicação (`JANELA` / `PORTA`).

Nos testes foi utilizado `DESIGN 60x111` com aplicação `JANELA`.

A v0.2 inferia aplicação a partir da folha; a v0.3 passa a pedir o campo explicitamente.

Isso corrige a quantidade das guarnições/barras chatas horizontais e explica cerca de R$ 37,98 da divergência do caso DESIGN.

## 5. Dois custos devem coexistir

Não devemos apagar o custo por consumo.

O software precisa manter:

### Custo técnico / consumo
Quanto material efetivamente entra na esquadria.

### Custo de aquisição
Quanto a empresa precisa desembolsar para comprar unidades inteiras de estoque.

Isso permite medir:
- sobra;
- aproveitamento;
- valor imobilizado em retalhos;
- custo econômico;
- fluxo de caixa de compras.

Mais adiante, retalhos em estoque poderão reduzir a quantidade de barras novas a comprar.
