# GR — Reverse engineering Fase 9

Status: **GR_ENGINE_0.9.0 — CANDIDATO À AUDITORIA FÍSICA**

## Escopo novo

A Fase 9 adiciona **janela GR Design 60x78 com vidro inteiro e DOBRADIÇA SISTEMA OB**.

Recorte liberado tecnicamente:

- aplicação: `JANELA`;
- folha: Design 60x78 abertura externa;
- 1 folha;
- `VIDRO INTEIRO`;
- fechamento: `MAÇANETA COM CREMONA SEM CHAVE`;
- dobradiça: `DOBRADIÇA SISTEMA OB`;
- cremona: obrigatoriamente escolhida pelo usuário entre as cremonas `OSCILO/GIRO` E:15 mm do catálogo;
- sem seleção automática de comprimento;
- sem tela, persiana, bandeiras, travessas ou reforço estrutural opcional.

Todo o escopo da Fase 8 permanece preservado.

## Fonte oficial

Workbook:

`SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256:

`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`

## Regra de dobradiça do XLSM

A aba GR usa:

`U3 = IF(U2="DOBRADIÇA SISTEMA OB",1,2)`

Com `U3=1`, as linhas de ferragem `GR!105:110` selecionam, uma unidade por folha, os materiais:

- `DOB6` — FALSO COMPASSO;
- `DOB7` — CORPO DA DOBRADIÇA;
- `DOB8` — CORPO E PINO DOBRADIÇA SUPERIOR;
- `DOB9` — DOBRADIÇA INFERIOR;
- `DOB10` — SUPORTE DA DOBRADIÇA INFERIOR;
- `DOB11` — CONJUNTO CAPAS DOBRADIÇA OSCILO.

Preços atuais do catálogo oficial:

- DOB6: R$ 18,00;
- DOB7: R$ 3,14;
- DOB8: R$ 10,00;
- DOB9: R$ 10,00;
- DOB10: R$ 30,00;
- DOB11: R$ 1,45.

Total do conjunto OB antes dos demais itens:

**R$ 72,59 por folha.**

## Cremona OB

Para fechamento tipo 3 — `MAÇANETA COM CREMONA SEM CHAVE` — a fórmula `GR!B112` usa diretamente `Q2`.

Por isso a Engine **não cria regra automática por altura** nesta fase. A seleção é explícita.

Catálogo `LISTAFERRA!67:71`:

- `CRE21` — CREMONA OSCILO/GIRO 400 mm E:15 mm — R$ 15,00;
- `CRE22` — CREMONA OSCILO/GIRO 900 mm E:15 mm — R$ 17,00;
- `CRE23` — CREMONA OSCILO/GIRO 1100 mm E:15 mm — R$ 18,00;
- `CRE24` — CREMONA OSCILO/GIRO 1400 mm E:15 mm — R$ 20,68;
- `CRE24` — CREMONA OSCILO/GIRO 1900 mm E:15 mm — R$ 25,52.

O XLSM contém a anomalia de cadastro de usar o mesmo código `CRE24` para 1400 e 1900 mm. A Engine preserva o código do catálogo e distingue os dois itens pela descrição e preço.

## Evidência ORCS

Foram encontrados **55 registros GR de janela Design 60x78 com DOBRADIÇA SISTEMA OB**.

Entre eles:

- 48 com vidro inteiro;
- 7 com painel completo;
- 40 com `MAÇANETA COM CREMONA SEM CHAVE`.

A maioria dos registros antigos não gravou o campo Q da cremona. Existe um registro explícito utilizável para provar a família:

### ORCS 4572

- 800 x 1000 mm;
- janela GR Design 60x78;
- 1 folha;
- vidro `06mm TEMPERADO INCOLOR`;
- `DOBRADIÇA SISTEMA OB`;
- `MAÇANETA COM CREMONA SEM CHAVE`;
- `CREMONA OSCILO/GIRO COMP. 1100mm E:15mm`.

O registro é identificado como `TESTE` no histórico; por isso ele é usado como **evidência explícita de fórmula/configuração**, não como confirmação isolada de padrão físico de produção.

## Geometria do golden ORCS 4572

Com 800 x 1000 mm:

- folha final: 736 x 936 mm;
- vão de baguete: 616 x 816 mm;
- vidro: 608 x 808 mm;
- 1 vidro.

As regras de vidro, baguete e vedações são idênticas às da Fase 8.

## Vedações

A Fase 9 preserva a regra física confirmada pela fabricação:

- `ACB606` — borracha de vidro/lambri no perímetro do preenchimento;
- `AC0002` — borracha redonda na folha por fora;
- `AC0002` — borracha redonda no marco por dentro.

Para o golden 800 x 1000:

**custo de vedações = R$ 15,856000**

## Parafusos da ferragem OB

`GR!G119`:

`(G105*8)+(G111+G112+G114)*2`

No Sistema OB:

- G105 = 1;
- G111 = 1;
- G112 = 1;
- G114 = 2.

Resultado:

**16 parafusos PAR1**

A Fase 9 preserva exatamente essa fórmula.

## Custo físico atual congelado

ORCS 4572 reconstruído com catálogo atual, vedações físicas corrigidas e cremona 1100 mm:

**R$ 656,427160**

O AO histórico não é usado como golden de preço atual.

## Gate físico ainda aberto

A implementação é tecnicamente reproduzível pelo XLSM e pelo registro ORCS explícito, mas falta uma confirmação de fabricação para transformar o recorte em homologação física completa:

> Em janela GR com DOBRADIÇA SISTEMA OB, a família usada em produção é sempre a `CREMONA OSCILO/GIRO` (CRE21/CRE22/CRE23/CRE24), escolhendo apenas o comprimento conforme a peça?

Enquanto isso não for confirmado:

- a v0.9 permanece **CANDIDATO À AUDITORIA FÍSICA**;
- a Engine exige seleção explícita da cremona;
- não existe regra automática de tamanho;
- não liberar plano de compras/corte GR.

## Compra/corte

Continua bloqueado.

A Fase 9 cobre custo técnico/BOM, não a semântica definitiva de estoque e corte GR.
