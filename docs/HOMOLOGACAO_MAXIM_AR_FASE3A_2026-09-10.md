# Homologação técnica — Maxim-Ar Fase 3A

Data: 2026-09-10

Branch: `feature/maxim-ar-engine-v3`

Base exata: `ce7c9c9addde3d8ab076e188b7c2906d37244071`

Engine preservada: `MX_ENGINE_0.2.0`

## Resultado executivo

A investigação foi concluída, mas nenhum dos seis bloqueadores recebeu prova
física suficiente para virar regra produtiva. O XLSM e o histórico permitem
confirmar inconsistências e delimitar candidatos; não permitem inferir a
construção correta. A Engine, a API e a Web não foram alteradas.

Fonte oficial: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`

SHA-256 confirmado: `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`

## Matriz de homologação

| Bloqueador | Status | Evidência Excel | Evidência ORCS | Evidência física | Regra candidata | Confiança | Próxima ação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Vedações DESIGN | BLOCKED | MX 67:69 restringe três vedações ao PRIME; catálogo traz `AC0708` a R$ 1,80/m, sem ligação MX/percurso | 2.423 descrições DESIGN; custo agregado não identifica BOM | ausente | `AC0708` é candidato por catálogo/analogia CR, mas material e percursos de vidro/folha/marco não estão provados | BAIXA | obter lista/foto de uma fabricação DESIGN |
| Travessas AF/AG da folha | BLOCKED | `G12/G13` multiplicam vidro/baguete; não há linha de perfil, reforço ou vedação correspondente | AF=0 e AG=0 em 3.644 MX | ausente | provavelmente requer travessa PRIME `PR4263` ou DESIGN `DE6072` e reforço, mas dimensões/encontros não estão provados | BAIXA | obter folha real dividida ou confirmação de opção não fabricável |
| Bandeiras complexas | PARTIAL | fórmulas existem, mas ignoram travessas verticais e `G18` usa `AI` inferior no painel superior | 119 casos com bandeira + múltiplas folhas ou travessas; registros provam uso comercial, não fabricação correta | ausente | modelar bandeira como grade de vãos somente após desenho/lista de corte real | MÉDIA | confrontar ORCS 5959, 8696 e 10075 com produção |
| Módulos separados + travessas | PARTIAL | quantidade cresce por travessas, dimensões não são subdivididas; `G30:G31` usa `AH/AI` em vez de `AJ/AK` | 13 módulos separados; seis com travessas (ORCS 61, 75, 76, 1073, 18214, 18306) | ausente | cada módulo deve ter quadro e grade próprios, mas folgas e cortes físicos faltam | MÉDIA | obter desenho e listas dos seis casos |
| Calços de bandeiras | BLOCKED | `MX!G72=G10*2` conta somente folhas móveis; CR usa `SUM(G84:G94)*2`, por painel, mas é outra família | ORCS não registra BOM/acessório por painel | ausente | adicionar calços por vidro fixo é plausível; quantidade/posição não comprovadas | BAIXA | contar calços em bandeira real e validar `AC0312` |
| Reforço ALUM10238/ALUM15338 | BLOCKED | catálogo: 102 × 50 e 138 × 50, ambos R$ 46/m; MX usa largura total, uma peça por bandeira; desconto de 50 mm só para 102 em módulo separado | zero registro preenchido em 3.644 MX | ausente | regra de planilha está inventariada, mas critério de seleção e instalação não têm prova física | BAIXA | obter caso real, FFD e critério estrutural |

Status de evidência: vedações, AF/AG, calços e reforço permanecem
`PENDING_PHYSICAL_HOMOLOGATION`; bandeiras complexas e módulos separados são
`LEGACY_AMBIGUOUS`, com erros de referência/consistência demonstrados. A
existência de uma fórmula ou de um custo histórico não foi tratada como prova
de fabricação.

## Auditoria sistemática da ORCS

O script `tools/audit_maxim_ar_phase3a.py` lê OpenXML sem Excel, identifica MX
por `ORCS!X="MX"` e nunca emite cliente, nome, item, local, código comercial ou
descrição comercial. Resultado do XLSM oficial:

| Medida | Resultado |
| --- | ---: |
| Registros MX | 3.644 |
| AF não nulo | 0 |
| AG não nulo | 0 |
| Alguma bandeira | 539 |
| Bandeira inferior | 483 |
| Bandeira superior | 163 |
| Bandeira complexa (múltiplas folhas ou alguma travessa) | 119 |
| Múltiplas folhas | 508 |
| Tela | 593 |
| Módulos separados | 13 |
| Módulos separados com travessa | 6 |
| Reforço estrutural preenchido | 0 |

Distribuição de folhas: 1: 3.136; 2: 374; 3: 91; 4: 33; 5: 2; 6: 3;
7: 2; 8: 3. Sistemas: PRIME 1.221 e DESIGN 2.423 (inclui duas grafias DESIGN
fora do texto canônico). Orientações: 3.591 horizontal e 53 vertical.

Travessas de bandeira: `AH` 78, `AI` 1, `AJ` 54 e `AK` 10. Os casos de módulo
separado com travessa são os IDs técnicos ORCS 61, 75, 76, 1073, 18214 e
18306. Casos úteis para confronto físico: 5959 (duas bandeiras com travessas
verticais), 8696 (bandeira superior com três travessas horizontais) e 10075
(duas folhas, duas bandeiras e travessas H/V).

## 1. Vedações DESIGN

### Evidência

- `MX!B67:B69` e `G67:G69` habilitam borracha de vidro `ACB606` e borracha
  Maxim-Ar `AC0002` somente quando a folha é PRIME. DESIGN produz zero.
- `LISTAPERFIS!A54:C54` contém `AC0708`, “BORRACHA DESIGN 7X8”, R$ 1,80/m.
- CR seleciona `AC0708` para sua variante DESIGN em `CR!B108`, usando o
  perímetro dos painéis em `G108`. Isso é analogia de outra família, não prova
  do encaixe/percurso em Maxim-Ar.
- Nomes definidos apenas apontam para tabelas amplas (`LISTAP`, `PAFAB` etc.);
  nenhum nome cria regra oculta MX. O projeto VBA não contém os códigos de
  material pesquisados.
- Os 2.423 registros DESIGN guardam somente custo agregado. Recalcular pelo
  XLSM continua zerando vedações, portanto o histórico não revela material.

Conclusão: alternativa C, evidência insuficiente. Classificação
`PENDING_PHYSICAL_HOMOLOGATION`. `AC0708` é candidato, não regra.

## 2. Travessas AF/AG dentro da folha móvel

`MX!G12` e `G13` usam AF/AG para multiplicar baguetes e, por consequência,
`G59=G12/2` multiplica vidros. Cotas auxiliares podem alterar alguns ramos, mas
não existe no BOM MX uma linha que gere o perfil da travessa, seu reforço, seus
cortes ou vedação adicional. O perfil `PR4263`/`DE6072` aparece como travessa
de folhas/bandeiras em outros ramos, mas não há vínculo suficiente para AF/AG.

A busca integral encontrou AF=0 e AG=0 nos 3.644 registros. O snapshot antigo
de 773 MX também tem zero. Classificação `LEGACY_AMBIGUOUS` e
`PENDING_PHYSICAL_HOMOLOGATION`.

## 3. Bandeiras complexas

O histórico contém 119 configurações complexas e demonstra que foram orçadas,
mas não fornece BOM físico. As fórmulas não fecham uma grade cartesiana:

- no módulo único, `G16/G18` calcula baguetes por travessas horizontais e
  separadores entre folhas, sem usar `AH/AJ` para criar as colunas de vidro;
- `G18` usa `AI` (inferior) no painel superior, embora a altura use `AK`;
- entradas órfãs também existem: ORCS 4299 tem `AJ=AK=800` sem bandeira
  superior, e por isso os valores são ignorados.

Casos históricos não provam que o resultado calculado corresponde ao item
instalado. Classificação `LEGACY_AMBIGUOUS`; status PARTIAL porque o defeito do
Excel foi comprovado, mas a regra física correta não.

## 4. Módulos separados e prova geométrica

Para a bandeira inferior separada, o Excel calcula:

```text
colunas = AH + 1
linhas  = AI + 1
quantidade de vidros = (AH + 1) × (AI + 1)     [G24/2 -> G60]
largura de cada vidro = D24 - folga             [D60]
altura de cada vidro  = D25 - folga             [E60]
```

Porém `D24` não divide a largura por `AH+1`, e `D25` não divide a altura por
`AI+1`. Portanto, ao adicionar uma travessa, a quantidade é multiplicada mas
cada vidro conserva a dimensão do vão não subdividido. Com `AH=1`, por exemplo,
o Excel pede dois vidros de largura inteira em vez de dois vidros com larguras
que somem ao vão disponível.

No painel superior, perfis usam `AJ/AK` em `G28/G29`, mas baguetes/vidros usam
novamente `AH/AI` em `G30/G31`. Assim, duas bandeiras com divisões diferentes
não podem produzir simultaneamente quantidades coerentes.

Isso é `LEGACY_BUG_CONFIRMED` quanto à matemática do XLSM. Ainda é
`PENDING_PHYSICAL_HOMOLOGATION` para definir folgas, encontros e cortes reais.

## 5. Calços físicos

MX seleciona `AC0312` (R$ 0,35/un) e usa `G72=G10*2`: quatro calços por folha
móvel na configuração básica, independentemente de bandeiras, quantidade de
vidros fixos, área, orientação, travessas ou módulos. CR usa outra expressão,
`SUM(G84:G94)*2`, equivalente a dois calços por painel contado naquela família.
A divergência entre famílias impede copiar a regra.

O histórico ORCS não contém detalhe de acessórios. Classificação
`LEGACY_AMBIGUOUS` e `PENDING_PHYSICAL_HOMOLOGATION`.

## 6. Reforços estruturais

`LISTAPERFIS!35:36` registra:

- `ALUM10238`: perfil estrutural de alumínio 102 × 50 mm, R$ 46/m;
- `ALUM15338`: descrição 138 × 50 mm, R$ 46/m (o código e a descrição não
  expressam a mesma largura nominal).

Em MX, `B32=R2`, `D32=D8`, `G32=J32+K32`, `J32=1` com bandeira inferior e
`K32=1` com superior. Logo há um corte na largura total por bandeira. Apenas
`REFORÇO 102X50MM` em módulos separados aciona `U3=50`, reduzindo a altura do
quadro separado; o corte estrutural em `D32` não recebe esse desconto.

Nenhum registro MX tem `R` preenchido com reforço. Por exigência da fase, a
classificação é `PENDING_PHYSICAL_HOMOLOGATION`.

## Arquivos temporários

O snapshot íntegro de 773 MX repete as fórmulas oficiais e não traz AF/AG ou
reforço. Dois fragmentos ZIP sem diretório central e um arquivo vazio foram
analisados sem gravação. As partes técnicas recuperáveis repetem as mesmas
ambiguidades. Detalhes e hashes estão em
`docs/ANALISE_ARQUIVOS_TMP_MAXIM_AR_FASE3A_2026-09-10.md`.

## Decisão

Os seis temas foram investigados até o limite das fontes locais. A Fase 3A
pode ser fechada como investigação concluída, mas a Fase 3B integral não deve
implementar nenhuma dessas regras antes do retorno da fábrica/orçamento. O
pedido objetivo está em `docs/EVIDENCIAS_NECESSARIAS_MAXIM_AR_FASE3.md`.

**Bloqueadores tecnicamente resolvidos: 0/6.**

## Regressão final

- Engine: 85 testes aprovados, 218 subtestes; CR 57 preservados; Maxim-Ar 28
  preservados (Fase 1: 16, Fase 2: 12).
- API: 20 testes aprovados.
- Web: build Vite aprovado, 30 módulos transformados.
- Auditoria: compilação Python, `git diff --check`, hash oficial e contagens
  ORCS verificados.
- Falhas de produto: 0. As tentativas iniciais com `pytest` e `npm.ps1` não
  executaram por configuração local; os runners previstos (`unittest` e
  `npm.cmd`) foram executados com sucesso.
