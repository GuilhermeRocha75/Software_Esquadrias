# GR — Reverse engineering Fase 18

Status: **GR_ENGINE_0.18.0 — CANDIDATO À AUDITORIA**

## Escopo novo

A Fase 18 compõe simultaneamente:

- bandeira inferior simples;
- bandeira superior simples.

Primeiro recorte homologável:

- janela GR Design 60x78;
- 1 folha;
- VIDRO INTEIRO;
- módulo único;
- dobradiça 90 mm;
- fechamento com cremona;
- sem tela;
- sem persiana;
- sem subdivisões internas;
- sem reforço estrutural opcional.

As bandeiras simples isoladas das Fases 15–17 continuam preservadas.

## Evidência ORCS

Golden principal:

### ORCS 16482

- 400x2000 mm;
- janela 1 folha;
- Design 60x78 abertura externa;
- bandeira inferior 400 mm;
- bandeira superior 400 mm;
- vidro 4 mm Mini Boreal;
- dobradiça 90 mm;
- sem tela;
- sem persiana;
- descrição histórica: `JANELA 1 FOLHA DE GIRO + BANDEIRA INFERIOR (00) E SUPERIOR (00) (BRANCO)`;
- AO histórico: R$ 811,69.

O campo Q da cremona está vazio no ORCS.

Para tornar o golden financeiro atual determinístico, a v0.18 seleciona explicitamente:

`CREMONA 2 PONTOS COMP. 800mm E:15mm`

Essa escolha é compatível com a confirmação física anterior de que a cremona 800 mm é o padrão predominante das janelas de giro 90 mm, mas o custo AO histórico não é usado como paridade financeira direta.

## Fórmulas legadas relevantes

Com as duas bandeiras:

`GR!G19 = J19 + K19 = 2`

Portanto existem fisicamente:

- 1 travessa DE6072 separando a bandeira inferior da folha;
- 1 travessa DE6072 separando a folha da bandeira superior.

O marco externo de janela continua com:

`G8 = 2`

ou seja:

- 2 horizontais externos DE6058;
- 2 montantes verticais DE6058.

## Bug legado — dupla subtração AA2 + AB2

No módulo único:

`GR!D9 = E2 - V3`

Porém o caminho combinado de `GR!K11` contém nova subtração de:

`AA2 + AB2`

No caminho legado alternativo, D9 também pode receber AA2/AB2 quando Y3>0.

A Engine não replica a dupla subtração. Ela compõe a geometria física dos perfis:

- face do marco: 40 mm;
- travessas DE6072: 18 mm cada;
- overlaps da folha: 8 mm.

Para janela 1 folha com bandeira inferior e superior:

`H_folha = H_total - H_inferior - H_superior - 42`

No ORCS 16482:

`2000 - 400 - 400 - 42 = 1158 mm`

Classificação:

**LEGACY_BUG_CONFIRMED_BY_COMPOSED_TOPOLOGY**

## Referência E40

As fórmulas de altura dos fixos em `GR!D26` e `GR!D28` usam `LISTAPERFIS!E40`, referência que não fornece a dimensão necessária no workbook oficial.

A recuperação já homologada nas Fases 15–17 permanece:

`largura_vão = W - 80`

`altura_vão = H_bandeira - 58`

Vidro:

`largura_vidro = W - 88`

`altura_vidro = H_bandeira - 66`

Para cada bandeira de 400 mm no golden:

- vão fixo = 320x342 mm;
- vidro = 312x334 mm.

## Geometria principal — ORCS 16482

Entrada:

- W = 400 mm;
- H = 2000 mm;
- inferior = 400 mm;
- superior = 400 mm.

Resultado:

- marco externo = 400x2000 mm;
- folha móvel = **336x1158 mm**;
- vidro principal = **208x1030 mm**;
- travessa inferior = **332 mm**;
- travessa superior = **332 mm**;
- vão fixo inferior = **320x342 mm**;
- vão fixo superior = **320x342 mm**;
- vidro inferior = **312x334 mm**;
- vidro superior = **312x334 mm**.

## Perfis das bandeiras

Cada limite usa:

- 1x DE6072;
- 1x RAG - DE6072.

Total:

- **2 travessas DE6072**;
- **2 reforços RAG-DE6072**.

O marco externo permanece com os 2 horizontais DE6058 próprios da janela.

## PAR2

A v0.18 reproduz a topologia de `GR!G118`:

- G8 = 2;
- G10 = 2;
- G19 = 2.

Golden:

**PAR2 = 33,968**

## Vedações

Permanecem as regras físicas já confirmadas:

- ACB606 no vidro principal;
- AC0002 na folha;
- AC0002 no marco;
- ACB606 no vidro da bandeira inferior;
- ACB606 no vidro da bandeira superior.

Golden:

**R$ 18,842400**

## Custo técnico atual

Com cremona 800 mm explicitamente selecionada:

**R$ 849,551520**

O AO histórico de R$ 811,69 permanece apenas como evidência da configuração, pois o campo Q da cremona está vazio e o legado usa regras de bandeira corrigidas na Engine.

## API

A Fase 18 mantém os campos:

- `bottom_flag_height_mm`;
- `top_flag_height_mm`.

Quando ambos forem maiores que zero, a combinação `dual_flags` é ativada.

Escopo comercial exposto:

- JANELA;
- 1 folha;
- Design 60x78;
- vidro inteiro;
- dobradiça 90 mm;
- sem tela;
- sem persiana;
- sem divisões internas.

## Compra/corte

Continua bloqueado para GR.

## Gate técnico

Aprovar somente se:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–17;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre a main homologada.
