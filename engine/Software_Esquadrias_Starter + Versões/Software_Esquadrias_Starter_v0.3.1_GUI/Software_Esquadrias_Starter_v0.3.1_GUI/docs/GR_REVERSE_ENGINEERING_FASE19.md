# GR — Reverse engineering Fase 19

Status: **GR_ENGINE_0.19.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 19 inicia as subdivisões internas de bandeiras/fixos.

Primeiro recorte homologável:

- porta GR Design 60x104;
- abertura interna;
- 2 folhas;
- VIDRO INTEIRO;
- bandeira superior;
- 1 divisão vertical interna na bandeira superior;
- dobradiça 90 mm;
- sem tela;
- sem persiana;
- sem divisões internas nas folhas;
- sem reforço estrutural opcional.

Os quatro campos do histórico ORCS passam a ter representação explícita na Engine/API:

- AH → bottom_flag_vertical_transoms;
- AI → bottom_flag_horizontal_transoms;
- AJ → top_flag_vertical_transoms;
- AK → top_flag_horizontal_transoms.

Na Fase 19, somente:

`top_flag_vertical_transoms = 1`

é homologado.

## Evidência ORCS

Foram encontrados **9 registros GR** com alguma subdivisão de bandeira.

Distribuição:

- 6 casos com `AJ=1` — uma divisão vertical na bandeira superior;
- 1 caso com `AH=1`;
- 1 caso com `AH=2`;
- 1 caso com `AH=3`.

O caso mais limpo para iniciar é:

### ORCS 15295

- 1610x5220 mm;
- porta interna;
- 2 folhas;
- bandeira superior 2790 mm;
- AJ = 1;
- AK = 0;
- vidro 10 mm temperado incolor;
- monoponto;
- dobradiça 90 mm;
- sem tela;
- sem persiana;
- sem fixo lateral registrado;
- AO histórico: R$ 3.217,45871.

O AO histórico é usado apenas como evidência da configuração; o golden atual inclui correções físicas já homologadas e catálogo vigente.

## Fórmula da largura dos vãos

GR!D27:

`((D8 - 2*E19) - AJ*E18) / (AJ+1)`

Com:

- W = 1610;
- E19 = 40 mm;
- E18 = 36 mm;
- AJ = 1.

Logo:

`(1610 - 80 - 36) / 2 = 747 mm`

Cada vão da bandeira superior tem:

**747 mm de largura de baguete**

## Altura dos vãos

A referência `LISTAPERFIS!E40` continua inválida no workbook oficial.

A recuperação já homologada nas Fases 15–18 permanece:

`altura_vão = H_bandeira - 58`

Para 2790 mm:

**2732 mm**

## Divisor vertical

GR!D24:

`D28 + PFAB!B18`

Com:

- abertura = 2732 mm;
- PFAB!B18 = 12 mm.

Comprimento físico da travessa vertical:

**2744 mm**

Perfil:

- DE6072.

Reforço:

- RAG - DE6072.

## Baguetes — correção física

Com 1 divisor vertical existem 2 vãos.

Cada vão precisa de:

- 2 baguetes horizontais;
- 2 baguetes verticais.

Total físico:

- 4 baguetes horizontais de 747 mm;
- 4 baguetes verticais de 2732 mm.

O legado `GR!G27/G28` não representa o perímetro físico completo desses dois vãos.

Classificação:

**LEGACY_BUG_CONFIRMED_BY_GEOMETRY**

## Vidros

Cada vão:

- largura do vidro = 747 - 8 = **739 mm**;
- altura do vidro = 2732 - 8 = **2724 mm**.

Quantidade:

**2 vidros de bandeira**

A vedação ACB606 é calculada no perímetro dos dois vãos.

## Reforço e PAR2 do divisor

O XLSM não leva a travessa vertical interna da bandeira para `GR!G118`.

A fabricação já confirmou anteriormente que a travessa DE6072 utiliza o mesmo reforço e regra prática de fixação aproximadamente a cada 40 cm.

A Fase 19 usa:

`ceil(2744 / 400) = 7 PAR2`

adicionais ao valor já calculado pela Fase 16.

PAR2 total no golden:

**91,528**

Classificação:

**LEGACY_BUG_CONFIRMED_BY_PHYSICAL_RULE**

## Geometria principal — ORCS 15295

- marco externo: 1610x5220 mm;
- folha por lado: 763x2415 mm;
- vidro principal por folha: 583x2235 mm;
- quantidade de vidros principais: 2;
- bandeira superior: 2790 mm;
- divisor vertical: 2744 mm;
- vãos da bandeira: 2x 747x2732 mm;
- vidros da bandeira: 2x 739x2724 mm.

## Vedações

Com as regras físicas já confirmadas:

- vidros das duas folhas;
- borracha redonda folha/marco;
- dois vidros da bandeira.

Custo atual de vedações:

**R$ 86,132000**

## Custo técnico atual

Golden atual:

**R$ 5.594,460350**

## API

A Fase 19 adiciona:

- `bottom_flag_vertical_transoms`;
- `bottom_flag_horizontal_transoms`;
- `top_flag_vertical_transoms`;
- `top_flag_horizontal_transoms`.

Somente a combinação `0/0/1/0` é liberada nesta fase.

## Compra/corte

Continua bloqueado para GR.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–18;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre a main homologada.
