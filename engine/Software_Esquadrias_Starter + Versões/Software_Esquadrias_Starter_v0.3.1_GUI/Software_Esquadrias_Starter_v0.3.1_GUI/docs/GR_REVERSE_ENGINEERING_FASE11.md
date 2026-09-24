# GR — Reverse engineering Fase 11

Status: **GR_ENGINE_0.11.0 — APROVADO NO ESCOPO DA FASE 11**

## Escopo novo

A Fase 11 adiciona o primeiro recorte completo de persiana na família GR:

- modo: `MANUAL EM PAINEL ÚNICO`;
- caixa: `CAIXA DE 200MM`;
- tala: `TALA DE PVC 40MM`;
- preenchimento da esquadria: `VIDRO INTEIRO`;
- porta GR Design 60x104 nos recortes já homologados;
- janela GR Design 60x78 nos recortes já homologados;
- dobradiça 90 mm ou Sistema OB quando já permitido pela Engine base;
- sem tela, bandeiras ou reforço estrutural opcional.

Os modos motorizados e de 2/3 painéis permanecem bloqueados para fases seguintes.

## Evidência histórica ORCS

Foram encontrados **67 registros GR com persiana**.

Distribuição por modo:

- 44 — `MANUAL EM PAINEL ÚNICO`;
- 10 — `AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO`;
- 7 — `AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO`;
- 6 — `MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES`.

O modo manual em painel único é, portanto, o recorte histórico dominante e foi priorizado.

Referências congeladas:

- ORCS 18132 — porta 870x2160, vidro 6 mm, monoponto;
- ORCS 11111 — janela 500x1100, vidro 6 mm, cremona 800 mm.

Os custos AO históricos são usados apenas como evidência do legado, pois a planilha GR omite parte relevante do kit de persiana.

## Geometria comprovada no XLSM

A aba GR define:

- `V3 = 200` quando há persiana;
- marco principal: altura total menos 200 mm;
- caixa: `D47 = largura_total - 15`;
- guia lateral: `D48 = altura_total - 200`;
- tala, painel único: `D50 = largura_total - 2*32 - 10`;
- terminal: mesmo comprimento da tala;
- eixo: `D52 = largura_total - 40`.

Assim, para painel único:

- caixa = `W - 15`;
- guias laterais = `H - 200`;
- largura da tala = `W - 74`;
- eixo = `W - 40`.

A reserva de 200 mm reduz marco, folha e vidro, mas **não reduz os acabamentos externos/internos de altura**, que continuam referenciando a altura total da esquadria.

## Talas — correção física já homologada

O XLSM usa:

`G50 = H / 40`

e aceita quantidade fracionária.

Como cada tala é uma peça física, a Engine usa:

`ceil(H / 40)`

Essa mesma correção já foi homologada na persiana da família CR e usa o mesmo perfil `326015_F`.

Classificação:

**LEGACY_BEHAVIOR_CORRECTED**

## Kit físico manual

Perfis lineares GR explicitamente presentes:

- `321040` — caixa de persiana 200 mm;
- `327201` — guia lateral;
- `326015_F` — tala PVC 40 mm;
- `311712` — terminal de alumínio;
- `375021` — eixo 60 mm.

A v0.11 **não adiciona** `327019 PROLONGADOR DE GUIA`, porque esse perfil existe na CR mas não aparece no bloco de perfis da aba GR.

## Bug legado 1 — auxiliares inexistentes

As linhas `GR!85:102` listam os mesmos componentes físicos do kit de persiana da CR, porém várias fórmulas apontam para células auxiliares `143:156`.

A aba GR termina em `AU122`, portanto essas auxiliares não existem.

Isso impede que o XLSM atual calcule corretamente quantidades como:

- polia;
- ponteira;
- adaptador;
- recolhedor;
- passador;
- limitador.

A família CR possui a mesma estrutura e os mesmos códigos, com fórmulas completas e já homologadas.

Para `MANUAL EM PAINEL ÚNICO`, a v0.11 recupera:

- 2x `370113` — tampas laterais;
- 1x `371513_4` — placa de contenção da polia;
- 1x `371513_2` — placa de contenção da ponteira;
- 1x `375110` — polia;
- 1x `375213` — ponteira;
- 1x `375234` — adaptador;
- 1x `375339` — recolhedor embutido;
- 1x `373128` — convite para guias;
- 2x `375678` — engate da primeira tala;
- 1x `375415` — passador frontal;
- 2x `375441` — limitadores.

Classificação:

**LEGACY_BUG_CONFIRMED_BY_STRUCTURE**

Não foi necessário solicitar nova resposta à fabricação porque a regra é recuperável pela própria base técnica já homologada da CR e pelos mesmos códigos explicitamente listados na GR.

## Bug legado 2 — subtotal da persiana

`GR!I103` é:

`SUM(I83:I84)`

Portanto o subtotal de acessórios soma apenas:

- calços;
- tapa-deságue.

Ele **ignora completamente GR!85:102**, onde estão eixo/acessórios da persiana.

A v0.11 inclui o kit físico completo no custo técnico.

Classificação:

**LEGACY_BUG_CONFIRMED**

## Golden — ORCS 18132

Configuração:

- porta 870x2160;
- abertura interna;
- 1 folha;
- vidro 6 mm temperado incolor;
- monoponto;
- dobradiça 90 mm;
- persiana manual em painel único.

Geometria física:

- vão principal abaixo da caixa: 1960 mm;
- folha: 806x1923 mm;
- vidro: 626x1743 mm;
- caixa: 855 mm;
- guias: 1960 mm;
- tala: 796 mm;
- 54 talas;
- eixo: 830 mm.

Custo de vedações:

**R$ 26,051600**

Custo do kit de persiana:

**R$ 706,531250**

Custo técnico atual:

**R$ 2.049,990250**

## Golden — ORCS 11111

Configuração:

- janela 500x1100;
- 1 folha;
- vidro 6 mm temperado incolor;
- cremona padrão 800 mm;
- dobradiça 90 mm;
- persiana manual em painel único.

Geometria:

- vão principal: 900 mm;
- folha: 436x836 mm;
- vidro: 308x708 mm;
- caixa: 485 mm;
- guias: 900 mm;
- tala: 426 mm;
- XLSM legado: 27,5 talas;
- Engine física: **28 talas**;
- eixo: 460 mm.

Custo de vedações:

**R$ 11,856000**

Custo do kit de persiana:

**R$ 412,949250**

Custo técnico atual:

**R$ 1.015,786410**

## Compra/corte

O plano de compras/corte GR continua bloqueado.

A Fase 11 calcula BOM e custo técnico da persiana, mas não promove ainda a família GR ao FFD de compras/corte.

## Gate técnico

Para aprovar a v0.11:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–10;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre a `main`.

Após esse gate, a próxima expansão natural é:

1. persiana automatizada em painel único;
2. persiana manual em 2 painéis/eixos independentes;
3. demais combinações somente depois.
