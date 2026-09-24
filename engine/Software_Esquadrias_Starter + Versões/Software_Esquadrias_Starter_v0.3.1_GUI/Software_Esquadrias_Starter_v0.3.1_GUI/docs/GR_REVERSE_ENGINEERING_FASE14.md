# GR — Reverse engineering Fase 14

Status: **GR_ENGINE_0.14.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 14 adiciona:

`TELA MOSQUITEIRA (RECOLHÍVEL)`

Código:

`TL3`

A tela é um componente independente e pode ser combinada com qualquer configuração GR já homologada pela Engine, inclusive persiana.

## Evidência histórica

Foram encontrados **21 registros GR com tela mosquiteira**.

Eles incluem:

- portas e janelas;
- 1 e 2 folhas;
- casos com e sem persiana;
- dobradiça 90 mm e Sistema OB;
- vidro e painel.

A Fase 14 não amplia estruturas ainda não homologadas; ela adiciona a tela apenas sobre configurações que a v0.13 já consegue calcular.

Caso histórico principal:

### ORCS 9894

- porta 900x2100;
- 1 folha;
- abertura externa;
- painel completo;
- monoponto;
- dobradiça 90 mm;
- tela mosquiteira;
- sem persiana.

O AO histórico é usado somente como evidência de configuração.

## Fórmula da tela no XLSM

A aba GR usa:

- `GR!B73 = TELA MOSQUITEIRA (RECOLHÍVEL)`;
- `GR!C73 = TL3`;
- `GR!J73 = LISTADIV!C5 = 110`;
- `GR!K73 = LISTADIV!C6 = 110`;
- `GR!L73 = LISTADIV!C7 = 110`.

Preço pretendido:

`largura_m * 110 + altura_m * 110 + 110`

Porém a GR usa:

- `GR!D73 = D4`;
- `GR!E73 = D5`.

Essas referências não carregam as dimensões reais do marco neste workbook.

## Recuperação da fórmula — LEGACY_BUG_CONFIRMED_BY_SHARED_FORMULA

A aba MX usa exatamente:

- o mesmo código `TL3`;
- a mesma descrição;
- os mesmos três preços `LISTADIV!C5:C7`;
- a mesma expressão de custo.

Mas referencia corretamente:

- largura do marco / 1000;
- altura do marco / 1000.

A Engine MX já está homologada com essa fórmula.

Assim, a v0.14 corrige GR para:

`largura_real_do_marco_m * 110 + altura_real_do_marco_m * 110 + 110`

Sem inferência externa e sem necessidade de nova consulta à fabricação.

## Dimensões da tela

A tela acompanha o marco efetivamente calculado pela GR:

- sem persiana: largura e altura total do marco;
- com persiana: largura do marco e altura útil **abaixo da caixa de 200 mm**.

Exemplo sem persiana 900x2100:

- tela = 900x2100 mm;
- custo = 0,9×110 + 2,1×110 + 110;
- custo tela = **R$ 440,00**.

Exemplo com persiana, porta 870x2160:

- marco útil = 870x1960 mm;
- custo = 0,87×110 + 1,96×110 + 110;
- custo tela = **R$ 421,30**.

## Golden ORCS 9894

Com catálogo e regras físicas atuais:

- base GR externa com painel: R$ 1.409,391705;
- tela TL3: R$ 440,000000;
- custo técnico total: **R$ 1.849,391705**.

O AO legado de ORCS 9894 não é usado como preço atual.

## Composição persiana + tela

A v0.14 também congela:

- porta 870x2160;
- vidro 6 mm;
- persiana manual em painel único;
- tela recolhível.

A tela usa 870x1960 mm, preservando a reserva de 200 mm da caixa.

Custo técnico total atual:

**R$ 2.471,290250**

## Compra/corte

Permanece bloqueado.

A tela TL3 está correta no BOM/custo técnico, mas a GR ainda não foi promovida ao plano unificado de compras/corte.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–13;
- CR/Maxim-Ar sem alteração interna;
- branch linear sobre main.
