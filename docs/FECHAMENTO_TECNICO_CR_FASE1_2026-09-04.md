# Fechamento técnico CR — Fase 1 — 2026-09-04

## Resultado

A Engine CR v0.4.0 implementa as regras de travessas, vidros subdivididos,
bandeiras inferior/superior, reforço estrutural e cotas numéricas estruturadas.
A BOM, os custos por consumo, a compra de barras e o plano de corte recebem os
novos componentes sem duplicar fórmulas na API.

Este fechamento não libera ainda as outras famílias: o gate integral do CR
continua dependendo da Fase 2 (persiana completa e combinações finais de tela)
e da decisão de importação do marcador legado `CR` descrita abaixo. A ausência
de infraestrutura SaaS não participa desse gate.

## Fontes confrontadas

- `Documento_Regras_Engenharia_CR_v0.1 (2).docx`, SHA-256
  `F55287A48BFF441B179CA17F280123E8E2810A6A995B0FC13736E72A6C439A12`;
- `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`, SHA-256
  `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`;
- auditoria de 2026-09-04, golden cases e regressões existentes.

O XLSM foi aberto por automação em modo invisível e somente leitura. Os casos
T26 a T34 foram recalculados com o Excel instalado, sem salvar o arquivo.

## Modelos adicionados

- `LeafGrid`: quantidades de travessas horizontais/verticais e cotas;
- `CustomDimension`: eixo, índice do vão e medida livre positiva;
- `FixedPanelConfiguration`: altura e grade da bandeira;
- `StructuralReinforcement`: material técnico explícito;
- `GridOpening`, `Transom`, `FixedPanelGeometry` e `GlassPanel`: saídas
  geométricas estruturadas;
- `GlassPanel[]`: lista dinâmica com origem, posição, dimensões, quantidade,
  área, material e custos;
- `source` na BOM e `source_position` nos cortes para rastrear cada vão;
- `kerf_mm` no plano de compra, com premissa padrão formal de `0 mm`.

## Regras implementadas

| Tema | Implementação |
|---|---|
| RF-CR-019/020 | Grade cartesiana; PRIME usa PR4263/RAG-PR4263 e DESIGN usa DE6072/RAG-DE6072 |
| RF-CR-027/028 | Bandeiras BOTTOM/TOP com DE6058, baguetes, vidros, travessas, reforços, BOM e cortes |
| RF-CR-029/032 | Reforço ALUM10238/ALUM15338; redução nomeada de 50 mm em cada bandeira |
| RF-CR-040/041/042 | Painéis de vidro derivados dos vãos, sem slots fixos vidro 1…9 |
| RF-CR-043/044/045/046 | Tela subdividida, baguetes, borrachas e escovas recalculadas |
| RF-CR-047/048/049/050 | Corta-vento, 2 calços/painel, tapa-deságue e limitadores |
| RF-CR-058 | Parafusos por perímetros com taxa nomeada de 4/m, sem quantidade negativa |
| Plano de corte | Novos perfis entram no FFD; barra padrão 5900 mm; kerf padrão 0 mm |

## Comparação Excel × Engine

Os totais abaixo usam acabamento interno e externo `AC3004` para permitir o
recálculo completo no arquivo legado. As dimensões, quantidades e custos dos
componentes válidos foram comparados, não apenas o total.

| Caso | Excel | Engine v0.4 | Explicação da diferença |
|---|---:|---:|---|
| T26 PRIME, 1 horizontal | 1.528,83176 | 1.528,91176 | +0,08: PAR2 negativo recusado |
| T26 DESIGN, 2 horizontais | 4.320,13218 | 4.320,21218 | +0,08: PAR2 negativo recusado |
| T27 PRIME, 1 vertical | 1.779,78072 | 1.779,86072 | +0,08: PAR2 negativo recusado |
| T27 DESIGN, 2 verticais | 5.184,03354 | 5.184,11354 | +0,08: PAR2 negativo recusado |
| T28 bandeira inferior | 1.866,84176 | 1.875,66576 | vedação da bandeira + correção PAR2 |
| T28-B inferior 1×1 | 3.320,35943 | 3.338,88903 | vedação dos 4 vãos + correção PAR2 |
| T29 bandeira superior | 1.867,00176 | 1.875,66576 | vedação, PAR2 e simetria de corte do reforço |
| T29-B superior 1×1 | 3.320,51943 | 3.338,88903 | vedação, PAR2 e simetria de corte do reforço |
| T34 sem reforço | 2.828,61110 | 2.847,63910 | vedação das duas bandeiras e simetria do reforço |
| T34-B com ALUM10238 | 3.020,05110 | 3.038,71910 | idem; bandeiras reduzidas 50 mm |

Diferenças deliberadas:

1. o Excel mantém `-50` para cada bandeira ausente em D38/D44 e reduz PAR2;
2. o Excel não soma vedação aos vãos das bandeiras, embora a bandeira deva ser
   entregue envidraçada e vedada; a Engine usa AC0708 porque DE6058/DE6072 são
   perfis da série DESIGN;
3. o Excel adiciona 5 mm somente ao reforço do marco da bandeira superior; a
   Engine aplica a mesma medida final de reforço nas posições TOP e BOTTOM;
4. em grade de folha com os dois eixos, G26 superconta travessas horizontais.
   A Engine usa a topologia física também comprovada nas bandeiras:
   `horizontais × colunas × folhas`, mais `verticais × folhas`.

## Testes

- Engine: **47 aprovados**;
- API: **5 aprovados**;
- total: **52 aprovados, 0 falhos**;
- a varredura de **192 configurações** do recorte anterior continua aprovada;
- compilação de `src`, `tests` e `api`: aprovada;
- plano combinado DESIGN, quantidade 2: 16 materiais em barra, 444 cortes,
  101 barras, 484.044 mm consumidos e 111.856 mm de desperdício nominal;
- golden anterior: **R$ 8.317,53971 antes e depois**, sem regressão;
- DE5013 continua fisicamente em 2 barras no caso histórico multi-item e o
  alerta continua restrito à assinatura comprovada.

## Status individual da Fase 1

| Funcionalidade | Status |
|---|---|
| Travessas horizontais | **VALIDADO** — PRIME e DESIGN, 1 e 2 travessas |
| Travessas verticais | **VALIDADO** — PRIME e DESIGN, 1 e 2 travessas |
| Vidros subdivididos | **VALIDADO** — lista dinâmica, área, custo, calços e tela |
| Bandeira inferior | **VALIDADO** — sem travessas e grade 1×1 |
| Bandeira superior | **VALIDADO** — sem travessas e grade 1×1 |
| Reforço estrutural | **VALIDADO** — desligado e ALUM10238, redução de 50 mm |
| Cotas manuais numéricas | **VALIDADO** — vãos livres explícitos e rejeição de soma inválida |
| Marcador legado `CR` em X2 | **BLOQUEADO PARA IMPORTAÇÃO** — ver abaixo |

## Bloqueio técnico isolado

O único significado comprovável de `X2="CR"` é operacional: ele força D18 a
zero. Não há no DOCX, nas fórmulas ou nos desenhos uma definição física da
medida que o marcador representa. Além disso, o XLSM usa W/X/AC de modo
diferente entre PRIME e DESIGN, deixa G16 sem fórmula e pode gerar largura
negativa e quantidades fracionárias nos vidros 2…9.

Por isso, a Engine aceita cotas numéricas como medidas livres indexadas nos
eixos `COLUMNS`/`ROWS`, mas não inventa uma conversão para o marcador `CR`.
Para liberar esse importador legado é necessário um desenho/caso preenchido
que defina a posição física correspondente ao marcador.

