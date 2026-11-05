# OP Fase A — comparação parcial reproduzível

**Não homologado.** Inputs reconstruídos e hipóteses estão em `op_reference_inputs.json` e no relatório JSON.
A igualdade é restrita aos campos transcritos. Não implica paridade da OP completa.

Casos: `{'igual': 10, 'input insuficiente': 2}`. Campos: `{'igual': 141, 'divergente': 2}`.

| Caso | Referência | Estado |
| --- | --- | --- |
| OP-GOLDEN-01 | op.pdf p1 | igual |
| OP-GOLDEN-02 | op.pdf p2 | igual |
| OP-GOLDEN-03 | op.pdf p3 | igual |
| OP-GOLDEN-04 | OP 2.pdf p1 | igual |
| OP-GOLDEN-05 | OP 2.pdf p2 | input insuficiente |
| OP-GOLDEN-06 | OP 2.pdf p3 | igual |
| OP-GOLDEN-07 | OP 2.pdf p4 | igual |
| OP-GOLDEN-08 | OP 2.pdf p5 | igual |
| OP-GOLDEN-09 | OP 2.pdf p6 | igual |
| OP-GOLDEN-10 | OP 2.pdf p7 | igual |
| OP-GOLDEN-11 | OP 2.pdf p8 | igual |
| OP-GOLDEN-12 | OP 3.pdf p1 | input insuficiente |

## OP-GOLDEN-01 — op.pdf p1

Engine: `CR_ENGINE_0.5.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR13852 | PR13852 | igual / MATCH |
| frame_width.final_length_mm | 1930 | 1930.0 | igual / MATCH |
| frame_width.cut_length_mm | 1935 | 1935.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 954 | 954.0 | igual / MATCH |
| leaf_width.cut_length_mm | 959 | 959.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 846 | 846.0 | igual / MATCH |
| glass.height_mm | 1294 | 1294.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |
| screen.width_mm | 846 | 846.0 | igual / MATCH |
| screen.height_mm | 1294 | 1294.0 | igual / MATCH |
| screen.quantity_total | 1 | 1.0 | igual / MATCH |

## OP-GOLDEN-02 — op.pdf p2

Engine: `CR_ENGINE_0.5.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR13852 | PR13852 | igual / MATCH |
| frame_width.final_length_mm | 1630 | 1630.0 | igual / MATCH |
| frame_width.cut_length_mm | 1635 | 1635.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 804 | 804.0 | igual / MATCH |
| leaf_width.cut_length_mm | 809 | 809.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 696 | 696.0 | igual / MATCH |
| glass.height_mm | 1294 | 1294.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |

## OP-GOLDEN-03 — op.pdf p3

Engine: `GR_ENGINE_0.25.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Uma folha DESIGN interna com painel; ferragens nao transcritas.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | DE6058 | DE6058 | igual / MATCH |
| frame_width.final_length_mm | 1160 | 1160.0 | igual / MATCH |
| frame_width.cut_length_mm | 1165 | 1165.0 | igual / MATCH |
| frame_width.quantity_total | 1 | 1.0 | igual / MATCH |
| leaf_width.code | DE60104 | DE60104 | igual / MATCH |
| leaf_width.final_length_mm | 1096 | 1096.0 | igual / MATCH |
| leaf_width.cut_length_mm | 1101 | 1101.0 | igual / MATCH |
| leaf_width.quantity_total | 2 | 2.0 | igual / MATCH |
| panel.quantity_total | 12.8357143 | 12.835714285714285 | igual / MATCH |

## OP-GOLDEN-04 — OP 2.pdf p1

Engine: `CR_ENGINE_0.5.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR8852 | PR8852 | igual / MATCH |
| frame_width.final_length_mm | 2800 | 2800.0 | igual / MATCH |
| frame_width.cut_length_mm | 2805 | 2805.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 1389 | 1389.0 | igual / MATCH |
| leaf_width.cut_length_mm | 1394 | 1394.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 1281 | 1281.0 | igual / MATCH |
| glass.height_mm | 1204 | 1204.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |

## OP-GOLDEN-05 — OP 2.pdf p2

Engine: `CR_ENGINE_0.5.0`. Estado: **input insuficiente**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.
- Modo de persiana e hipotese de comparacao; nao e selecao para fabrica.
- Modo de acionamento e arranjo/eixos da persiana nao informados na fixture.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR8852 | PR8852 | igual / MATCH |
| frame_width.final_length_mm | 1420 | 1420.0 | igual / MATCH |
| frame_width.cut_length_mm | 1425 | 1425.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 699 | 699.0 | igual / MATCH |
| leaf_width.cut_length_mm | 704 | 704.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 591 | 591.0 | igual / MATCH |
| glass.height_mm | 1214 | 1214.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |
| frame_height.final_length_mm | 1410 | 1410.0 | igual / MATCH |
| frame_height.cut_length_mm | 1415 | 1415.0 | igual / MATCH |
| frame_height.quantity_total | 2 | 2.0 | igual / MATCH |
| slat.cut_length_mm | 1346 | 1346.0 | igual / MATCH |
| slat.quantity_total | 40.25 | 41.0 | divergente / EXISTING_ENGINE_PHYSICAL_CORRECTION_CONDITIONAL_ON_SHUTTER_INPUT |

## OP-GOLDEN-06 — OP 2.pdf p3

Engine: `CR_ENGINE_0.5.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR8852 | PR8852 | igual / MATCH |
| frame_width.final_length_mm | 1160 | 1160.0 | igual / MATCH |
| frame_width.cut_length_mm | 1165 | 1165.0 | igual / MATCH |
| frame_width.quantity_total | 4 | 4.0 | igual / MATCH |
| leaf_width.code | PR4288 | PR4288 | igual / MATCH |
| leaf_width.final_length_mm | 580 | 580.0 | igual / MATCH |
| leaf_width.cut_length_mm | 585 | 585.0 | igual / MATCH |
| leaf_width.quantity_total | 8 | 8.0 | igual / MATCH |
| glass.width_mm | 428 | 428.0 | igual / MATCH |
| glass.height_mm | 1860 | 1860.0 | igual / MATCH |
| glass.quantity_total | 4 | 4.0 | igual / MATCH |

## OP-GOLDEN-07 — OP 2.pdf p4

Engine: `CR_ENGINE_0.5.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR8852 | PR8852 | igual / MATCH |
| frame_width.final_length_mm | 2480 | 2480.0 | igual / MATCH |
| frame_width.cut_length_mm | 2485 | 2485.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 1229 | 1229.0 | igual / MATCH |
| leaf_width.cut_length_mm | 1234 | 1234.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 1121 | 1121.0 | igual / MATCH |
| glass.height_mm | 884 | 884.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |

## OP-GOLDEN-08 — OP 2.pdf p5

Engine: `MX_ENGINE_0.3.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- DESIGN identificado por DE6078; uma folha inferida da quantidade de vidros.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | DE6058 | DE6058 | igual / MATCH |
| frame_width.final_length_mm | 530 | 530.0 | igual / MATCH |
| frame_width.cut_length_mm | 535 | 535.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | DE6078 | DE6078 | igual / MATCH |
| leaf_width.final_length_mm | 466 | 466.0 | igual / MATCH |
| leaf_width.cut_length_mm | 471 | 471.0 | igual / MATCH |
| leaf_width.quantity_total | 2 | 2.0 | igual / MATCH |
| glass.width_mm | 338 | 338.0 | igual / MATCH |
| glass.height_mm | 838 | 838.0 | igual / MATCH |
| glass.quantity_total | 1 | 1.0 | igual / MATCH |

## OP-GOLDEN-09 — OP 2.pdf p6

Engine: `CR_ENGINE_0.5.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR8852 | PR8852 | igual / MATCH |
| frame_width.final_length_mm | 1100 | 1100.0 | igual / MATCH |
| frame_width.cut_length_mm | 1105 | 1105.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 539 | 539.0 | igual / MATCH |
| leaf_width.cut_length_mm | 544 | 544.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 431 | 431.0 | igual / MATCH |
| glass.height_mm | 844 | 844.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |

## OP-GOLDEN-10 — OP 2.pdf p7

Engine: `MX_ENGINE_0.3.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- DESIGN identificado por DE6078; uma folha inferida da quantidade de vidros.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | DE6058 | DE6058 | igual / MATCH |
| frame_width.final_length_mm | 500 | 500.0 | igual / MATCH |
| frame_width.cut_length_mm | 505 | 505.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | DE6078 | DE6078 | igual / MATCH |
| leaf_width.final_length_mm | 436 | 436.0 | igual / MATCH |
| leaf_width.cut_length_mm | 441 | 441.0 | igual / MATCH |
| leaf_width.quantity_total | 2 | 2.0 | igual / MATCH |
| glass.width_mm | 308 | 308.0 | igual / MATCH |
| glass.height_mm | 838 | 838.0 | igual / MATCH |
| glass.quantity_total | 1 | 1.0 | igual / MATCH |

## OP-GOLDEN-11 — OP 2.pdf p8

Engine: `MX_ENGINE_0.3.0`. Estado: **igual**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- DESIGN identificado por DE6078; uma folha inferida da quantidade de vidros.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | DE6058 | DE6058 | igual / MATCH |
| frame_width.final_length_mm | 510 | 510.0 | igual / MATCH |
| frame_width.cut_length_mm | 515 | 515.0 | igual / MATCH |
| frame_width.quantity_total | 4 | 4.0 | igual / MATCH |
| leaf_width.code | DE6078 | DE6078 | igual / MATCH |
| leaf_width.final_length_mm | 446 | 446.0 | igual / MATCH |
| leaf_width.cut_length_mm | 451 | 451.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 318 | 318.0 | igual / MATCH |
| glass.height_mm | 848 | 848.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |

## OP-GOLDEN-12 — OP 3.pdf p1

Engine: `CR_ENGINE_0.5.0`. Estado: **input insuficiente**.

- Input reconstruido para comparar somente campos transcritos; confirmar input original.
- Fechamentos, vidro comercial e acabamentos usam defaults no snapshot; sem paridade integral de materiais.
- Duas folhas e sistema inferidos dos codigos e quantidades da referencia.
- Modo de persiana e hipotese de comparacao; nao e selecao para fabrica.
- Modo de acionamento e arranjo/eixos da persiana nao informados na fixture.

| Campo | PDF | Engine | Estado / motivo |
| --- | --- | --- | --- |
| frame_width.code | PR8852 | PR8852 | igual / MATCH |
| frame_width.final_length_mm | 1980 | 1980.0 | igual / MATCH |
| frame_width.cut_length_mm | 1985 | 1985.0 | igual / MATCH |
| frame_width.quantity_total | 2 | 2.0 | igual / MATCH |
| leaf_width.code | PR4266 | PR4266 | igual / MATCH |
| leaf_width.final_length_mm | 979 | 979.0 | igual / MATCH |
| leaf_width.cut_length_mm | 984 | 984.0 | igual / MATCH |
| leaf_width.quantity_total | 4 | 4.0 | igual / MATCH |
| glass.width_mm | 871 | 871.0 | igual / MATCH |
| glass.height_mm | 784 | 784.0 | igual / MATCH |
| glass.quantity_total | 2 | 2.0 | igual / MATCH |
| frame_height.final_length_mm | 980 | 980.0 | igual / MATCH |
| frame_height.cut_length_mm | 985 | 985.0 | igual / MATCH |
| frame_height.quantity_total | 2 | 2.0 | igual / MATCH |
| slat.cut_length_mm | 933 | 933.0 | igual / MATCH |
| slat.quantity_total | 59 | 60.0 | divergente / EXISTING_ENGINE_PHYSICAL_CORRECTION_CONDITIONAL_ON_SHUTTER_INPUT |
