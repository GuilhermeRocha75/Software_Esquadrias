# Fechamento técnico CR — Fase 2

Data: 2026-09-08

Branch: `feature/cr-complete-v2`

Base da Fase 1: `79fbd1bf3880469060c3063816481bcf5935c84b`

Engine: `CR_ENGINE_0.5.0`

## 1. Fontes e método

A fonte primária foi `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`. Foram
inventariadas as planilhas, fórmulas, VBA, listas de materiais e preços que
referenciam `PERSIANA`, `CAIXA`, `TALA`, `L2`, `M2` e `N2`. O formulário VBA
`CORRER` é a origem real das opções desses campos; `CR!L2:M2:N2` não possui
validação de dados nativa.

O arquivo `Documento_Regras_Engenharia_CR_v0.1.docx` não foi encontrado nas
pastas do projeto nem nas pastas legadas pesquisadas. Nenhuma regra foi
inventada para substituir essa ausência: o XLSM foi tratado como oráculo.

Escopo confirmado: somente CR. Fórmulas semelhantes encontradas em `PV` e
`GR` não foram migradas nesta fase.

## 2. Inventário das entradas de persiana

| Campo | Opções comprovadas | Origem |
|---|---|---|
| `CR!L2` | `SEM PERSIANA`; `MANUAL EM PAINEL ÚNICO`; `MANUAL EM 2 PAINÉIS COM EIXO ÚNICO`; `MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES`; `AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO`; `AUTOMATIZADA COM BOTOEIRA EM 2 PAINÉIS`; `AUTOMATIZADA COM BOTOEIRA EM 3 PAINÉIS`; `AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO`; `AUTOMATIZADA COM CONTROLE REMOTO EM 2 PAINÉIS`; `AUTOMATIZADA COM CONTROLE REMOTO EM 3 PAINÉIS` | VBA UserForm `CORRER` |
| `CR!M2` | `CAIXA DE 200MM` | VBA UserForm `CORRER` |
| `CR!N2` | `TALA DE PVC 40MM` | VBA UserForm `CORRER` |

`CR!L3` converte o modo em 0, 1, 2 ou 3 painéis. `CR!V3` vale 0 sem
persiana e 200 mm nos demais modos. `M2` é registrado pelo formulário, mas a
fórmula legada da caixa referencia diretamente `LISTAPERFIS!A65`; como existe
uma única opção, a Engine valida `M2` sem criar uma seleção inexistente.

## 3. Inventário técnico de materiais e fórmulas

| Campo/linha | Condição | Material | Código | Un. | Fórmula legada | Preço | Origem |
|---|---|---|---|---|---|---:|---|
| `L2`, CR 54 | persiana ativa | Caixa 200 mm | 321040 | m | comp. = largura - 15; qtd. = 1 | 102,93/m | CR!D54/G54; LISTAPERFIS A65 |
| `L2`, CR 55 | ativa | Guia lateral | 327201 | m | comp. = altura total - 200; qtd. = 2 | 40,00/m | CR!D55/G55; A66 |
| `L2`, CR 56 | mais de 1 painel | Guia central | 327204 | m | comp. = guia lateral; qtd. = painéis - 1 | 83,03/m | CR!D56/G56; A67 |
| `N2`, CR 57 | ativa | Tala PVC 40 mm | 326015_F | m | largura = `((L-2×32)-(p-1)×30)/p-10`; qtd. = `A/40×p` | 5,00/m | CR!D57/G57; A69; PFAB B13 |
| `L2`, CR 58 | ativa | Terminal de alumínio | 311712 | m | comp. = largura da tala; qtd. = painéis | 15,00/m | CR!D58/G58; A70 |
| `L2`, CR 59 | ativa | Eixo 60 mm | 375021 | m | `L-40`; independente: `L/2-40` | 26,67/m | CR!D59/G59; A71 |
| CR 60 | ativa por qtd. da guia | Prolongador de guia | 327019 | m | comp. e qtd. = guia lateral | 20,00/m | CR!D60/G60; A68 |
| CR 120 | ativa | Tampa lateral polia/ponteira | 370113 | un | manual 2; automatizada 1 | 44,95 | CR!G120; A75 |
| CR 121 | manual | Placa de contenção polia | 371513_4 | un | eixo único 1; independente 2 | 6,37 | CR!G121; A79 |
| CR 122 | ativa, não independente | Placa de contenção ponteira | 371513_2 | un | 1 | 7,10 | CR!G122; A78 |
| CR 123 | automatizada | Tampa lateral motor | 370141 | un | 1 | 44,99 | CR!G123; A73 |
| CR 124 | automatizada | Placa lateral motor | 371553 | un | 1 | 22,32 | CR!G124; A74 |
| CR 125 | multi, eixo único | Placa central eixo único | 371143 | un | painéis - 1 | 48,43 | CR!G125; A77 |
| CR 126 | manual independente | Placa central eixos independentes | 371127 | un | 1 | 78,27 | CR!G126; A76 |
| CR 127 | manual | Polia | 375110 | un | igual às placas de polia | 9,19 | CR!G127; A80 |
| CR 128 | ativa | Ponteira eixo 40 mm | 375213 | un | placa ponteira + 2×divisor independente | 9,00 | CR!G128; A84 |
| CR 129 | ativa | Adaptador 40/60 mm | 375234 | un | igual às ponteiras | 10,45 | CR!G129; A85 |
| CR 130 | manual | Recolhedor embutido | 375339 | un | igual às polias | 45,00 | CR!G130; A81 |
| CR 131 | controle remoto | Motor controle remoto | MOT1 | un | 1 | 500,00 | CR!G131; LISTAFERRA A48 |
| CR 132 | botoeira | Motor botoeira | MOT2 | un | 1 | 250,00 | CR!G132; LISTAFERRA A49 |
| CR 133 | ativa | Convite guias laterais (par) | 373128 | un | 1 | 9,44 | CR!G133; A72 |
| CR 134 | ativa | Engate da 1ª tala | 375678 | un | 2×painéis | 7,69 | CR!G134; A82 |
| CR 135 | manual | Passador frontal | 375415 | un | igual ao recolhedor | 4,00 | CR!G135; A83 |
| CR 136 | ativa | Limitador de abertura | 375441 | un | 2×painéis | 3,45 | CR!G136; A86 |

As linhas CR 112 e 113 (`Esc. guias da persiana` e `Esc. caixa da
persiana`) têm material, dimensão e fórmula de quantidade vazios, com
quantidade fixa zero. Não foram criados reforços sem evidência.

## 4. Modelagem e rastreabilidade

Foi criada `ShutterConfiguration` somente com os três campos comprovados:
`mode`, `box_description` e `slat_description`. `shutter_enabled` foi mantido
para compatibilidade: quando recebido sozinho, preserva exclusivamente o
desconto geométrico de 200 mm e emite `V0.2-SHUTTER-PARTIAL`; a API e o Web
novos enviam a estrutura explícita e recebem o kit completo.

Cada componente da persiana registra em `source` a célula de origem, por
exemplo `CR!D57/G57`. Os sete materiais lineares chegam a
`BAR_STOCK_CODES`, são explodidos em cortes físicos e passam pelo FFD de
5.900 mm. Ferragens e motores permanecem na compra exata não linear.

Sequência geométrica comprovada em `CR!D9`:

`altura útil = altura total - bandeira inferior - bandeira superior - 200`

## 5. Excel × Engine

| Regra/caso | Excel | Engine 0.5 | Resultado |
|---|---|---|---|
| Caixa | `L-15` × 1 | igual | conforme |
| Guias laterais | `A-200` × 2 | igual | conforme |
| Guia central | `(A-200)` × `(p-1)` | igual | conforme |
| Tala | largura exata do Excel | igual | conforme |
| Quantidade de talas | `A/40×p`, pode fracionar | `ceil(A/40)×p` | correção física deliberada |
| Eixo comum | `L-40` × 1 | igual | conforme |
| Dois eixos independentes | `(L/2-40)` × 1 | mesma medida × 2 | correção física deliberada |
| Divisor independente | Excel seleciona também divisor comum por texto `INDEPENDNETES` | somente 371127 | bug legado corrigido |
| Duas bandeiras + persiana, A=3400, 400+450 | 2350 mm | 2350 mm | conforme |
| Manual independente 2400×2200 | linhas 54:60 e 120:136 | persiana R$ 1.766,55245; total CR R$ 5.503,54007 | conforme, exceto correções acima |
| Remota 3 painéis 3000×3200 | motor MOT1 + kit de 3 painéis | persiana R$ 3.237,40925; total CR R$ 8.698,17887 | conforme |

## 6. Tela e combinação com vidros

No XLSM, os perfis do quadro usam quantidade equivalente ao número de folhas
e `TL1` usa `folhas/2`. Para 3 folhas isso produz três peças horizontais,
três verticais e fator 1,5, conjunto que não define quadros retangulares
físicos. A Engine separa as grandezas:

- `screen_panel_count` e `screen_frame_count`: `ceil(folhas/2)`, sempre inteiro;
- perfis, baguetes, escovas, roldanas e borracha: derivados dos quadros físicos;
- `screen_mesh_area_m2`: mantém exatamente o fator de consumo `folhas/2` do Excel;
- bandeiras não recebem tela;
- a grade das folhas subdivide vidro e tela sem multiplicar o quadro base;
- calços permanecem associados somente aos painéis de vidro.

A matriz certificada cobre PRIME janela, PRIME porta e DESIGN, cada qual com
2, 3, 4 e 6 folhas, nas combinações: simples; travessa horizontal; vertical;
ambos os eixos; bandeira inferior; superior; duas bandeiras; bandeira com
travessas; tela + persiana. Nenhum corte, dimensão ou quantidade física
negativa ou zero foi aceito.

## 7. Caso combinado de estresse

DESIGN 4200×3900, 4 folhas, quantidade 2, porta, vidro 8 mm, tela, persiana
remota de 3 painéis, travessas nos dois eixos, bandeiras 450/500 com grades,
reforço ALUM10238 e kerf 3 mm:

- altura útil principal: 2.750 mm;
- 24 painéis de vidro por unidade;
- 2 quadros físicos de tela e 4,089288 m² de malha;
- 124 linhas de BOM por unidade;
- custo técnico unitário: R$ 16.509,910218;
- custo técnico do pedido: R$ 33.019,820436;
- 309 barras no plano agregado;
- consumo técnico de barras: R$ 27.013,225300;
- compra de barras: R$ 32.120,308000;
- compra estimada total: R$ 38.126,903136;
- todos os cortes têm papel e item de origem e respeitam 5.900 mm com kerf.

## 8. Regressão, testes e golden

Execução final:

- Engine: 57 testes aprovados, 0 falhos;
- API: 7 testes aprovados, 0 falhos;
- total: 64 testes aprovados, 0 falhos;
- build Web/Vite: aprovado;
- novas matrizes determinísticas da Fase 2: 141 combinações internas;
- matriz histórica adicional: 192 combinações preservadas;
- golden técnico de quatro itens: R$ 8.317,53971, preservado;
- PAR2 negativo: não reproduzido;
- DE5013, FFD, 5.900 mm, kerf zero, travessas, bandeiras, reforço,
  cotas numéricas e vidros subdivididos: preservados.

## 9. Diferenças e bugs legados comprovados

1. `CR!G125` contém `EIXOS INDEPENDNETES`; por isso pode selecionar o divisor
   de eixo único no modo independente. A Engine não reproduz o componente
   indevido.
2. O modo de dois eixos independentes calcula meia largura, mas `CR!G59`
   registra uma peça. A Engine emite duas peças físicas.
3. `CR!G57` permite tala fracionária. A Engine arredonda a quantidade física
   para cima antes do FFD.
4. Tela de 3 folhas produz fator 1,5 no Excel. Ele foi mantido somente para a
   área da malha; quadros e perfis são inteiros.
5. O marcador textual legado `CR` das cotas segue documentado como ambíguo e
   não bloqueia cotas numéricas de geometria já suportadas.

## 10. Checklist de homologação

- [x] geometria 2/3/4/6, PRIME janela, PRIME porta e DESIGN
- [x] vidro, vidros subdivididos, baguetes e calços
- [x] ferragens, borrachas, escovas e acabamentos
- [x] travessas horizontais, verticais e nos dois eixos
- [x] bandeira inferior, superior e duas bandeiras
- [x] reforço estrutural e cotas manuais numéricas
- [x] tela 2/3/4/6, com travessas, bandeiras e persiana
- [x] persiana completa e persiana com bandeiras
- [x] BOM, custos por grupo e custo técnico
- [x] compra de barras, plano de corte, FFD e kerf
- [x] golden anterior e nenhuma regressão

## 11. Parecer final

Todos os critérios automatizáveis e todas as regras comprováveis na fonte
primária foram aprovados. A conclusão técnica fica sujeita à auditoria
independente solicitada antes de qualquer merge em `main`.

**CR — CORRER 100% HOMOLOGADO**

**GATE CR: APROVADO**

**É seguro iniciar as demais famílias: SIM**
