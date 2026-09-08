# Auditoria técnica do módulo CR — 2026-09-04

> Documento histórico do estado anterior à implementação. A Fase 1 foi
> implementada e revalidada em
> [FECHAMENTO_TECNICO_CR_FASE1_2026-09-04.md](FECHAMENTO_TECNICO_CR_FASE1_2026-09-04.md).

## 1. Estado geral

**CR: validado no recorte base já migrado, mas o módulo integral não pode ser
declarado 100% validado.**

O recorte base compreende esquadrias sem travessas, sem bandeira superior ou
inferior, sem cotas manuais e sem o kit completo de persiana. Nesse recorte, a
geometria, BOM, custos, compra de barras e plano de corte ficaram consistentes
com as regras conhecidas e com os casos legados disponíveis.

Não foi atribuído um percentual ao CR completo porque isso produziria uma
precisão artificial: o arquivo `.xlsm` não está no workspace e não existe um
inventário completo e mensurável de todas as regras CR do Excel.

### Critério de liberação em duas camadas

Esta auditoria separa explicitamente:

1. **Camada 1 — Engenharia / Engine CR:** é o gate para iniciar Maxim-Ar, Giro,
   Fixo, Pivotante e as demais famílias. Inclui todas as regras e combinações
   técnicas, geometria, BOM, custos, vidro, tela, persiana, reforços, barras,
   plano de corte e regressão;
2. **Camada 2 — Infraestrutura SaaS:** PostgreSQL, autenticação, usuários,
   permissões, multiempresa, preços por empresa, snapshots, persistência de
   clientes/obras/orçamentos, contratos, financeiro, estoque e módulos
   administrativos. Esses itens estão fora do gate desta auditoria.

**Resultado do gate da Camada 1: REPROVADO por pendências técnicas do próprio
CR.** A ausência da Camada 2 não contribuiu para esse resultado.

### Limites da evidência

- checkout auditado: `main`, commit `866f7c3`; a branch citada no pedido,
  `feature/api-v0.1`, existe e possui commits posteriores;
- Engine carregada pela API: v0.3.1 no caminho versionado atual;
- o Excel `SOFTBETA_ PERFIL PRE DELL AMANDA...xlsm` não foi encontrado;
- a comparação Excel × Engine ficou limitada aos CSV/JSON, diagnósticos e
  valores de referência presentes no repositório e fornecidos no pedido;
- a issue de fechamento do CR não está no checkout e a API não autenticada do
  GitHub respondeu `404`, compatível com repositório/issue sem acesso público.

## 2. Testes executados

### Resultado final

- Engine: **31 testes aprovados**;
- API/ponte da Engine: **3 testes aprovados**;
- total: **34 testes aprovados, 0 falhos**;
- dentro da suíte há uma varredura adicional de **192 configurações CR**,
  reunidas também em um único plano de compra para testar consolidação;
- compilação de `src`, `tests` e `api`: aprovada;
- `pytest` não está instalado; foi usado o runner oficial existente no projeto,
  `unittest`.

O baseline antes da auditoria tinha 8 testes. Todos passavam, mas não cobriam a
matriz exigida e o fixture chamado de pedido real ainda usava DESIGN no quarto
item, enquanto o golden técnico atual usa PRIME. O fixture antigo foi preservado
e renomeado conceitualmente como caso histórico DE5013.

### Matriz nominal sistema × folhas

| Sistema | 2 folhas | 3 folhas | 4 folhas | 6 folhas |
|---|:---:|:---:|:---:|:---:|
| PRIME janela 42×66 | aprovado | aprovado | aprovado | aprovado |
| PRIME porta 42×88 | aprovado | aprovado | aprovado | aprovado |
| DESIGN 60×111 | aprovado | aprovado | aprovado | aprovado |

As configurações da matriz distribuem:

- aplicação `JANELA` e `PORTA` independentemente do perfil da folha;
- larguras de 1.500 a 5.200 mm e alturas de 1.200 a 2.600 mm;
- quantidades 1, 2 e 3;
- vidros de 4, 5, 6 e 8 mm;
- os três modos de fechamento;
- cremonas de 1 ponto e 2 pontos de 400 a 1.600 mm;
- roldanas de 30, 50, 80, 120 e 150 kg;
- acabamento interno, externo e sem acabamento;
- tela ligada/desligada;
- persiana ligada/desligada.

### O que cada cenário matricial verifica

1. geometria e medidas finais;
2. medidas de corte com solda de 5 mm;
3. código, papel, comprimento e quantidade de cada perfil;
4. interlocks, DE5013, fechamento central, trilhos e perfis DESIGN;
5. baguetes por sistema e espessura do vidro;
6. reforços de marco e folha;
7. vidro, tela, borrachas e escovas;
8. acessórios e ferragens, incluindo códigos de cremona/fecho/roldana;
9. acabamentos e a diferença de quantidade horizontal por aplicação;
10. BOM completa e multiplicação pela quantidade comercial;
11. custo de cada componente, custo por grupo e custo técnico total;
12. explosão dos cortes e FFD independente por material;
13. quantidade de barras, cortes por barra e origem do item;
14. consumo, compra, desperdício, aproveitamento e custo de aquisição;
15. invariantes: nenhuma quantidade/custo negativo e nenhuma barra acima do
    comprimento de estoque.

## 3. Golden case atual

Configuração confirmada:

1. PRIME 42×66, JANELA, 2 folhas, 3500×2000, qtd 1;
2. DESIGN 60×111, JANELA, 2 folhas, 2000×2000, qtd 1;
3. PRIME 42×66, JANELA, 2 folhas, 1500×3000, qtd 1;
4. PRIME 42×66, JANELA, 2 folhas, 2000×2000, qtd 1.

Custos técnicos da Engine por item:

| Item | Custo |
|---:|---:|
| 1 | R$ 2.108,90036 |
| 2 | R$ 2.694,73947 |
| 3 | R$ 1.984,92952 |
| 4 | R$ 1.528,97036 |
| **Total Engine** | **R$ 8.317,53971** |
| Total Excel legado | R$ 8.317,21971 |
| Diferença intencional | **R$ 0,32000** |

O teste documenta explicitamente que o total legado é reproduzido ao subtrair
R$ 0,08 de cada um dos quatro itens. A Engine mantém `PAR2 >= 0` e não copia a
quantidade negativa do Excel.

Plano de compra da Engine para esse golden:

| Métrica | Resultado |
|---|---:|
| materiais em barra | 19 |
| cortes | 181 |
| barras | 70 |
| consumo | 340,162 m |
| compra | 413,000 m |
| desperdício | 72,838 m |
| aproveitamento global | 82,363680% |
| custo por consumo das barras | R$ 6.427,70140 |
| custo de compra das barras | R$ 8.201,53100 |
| custo exato dos demais materiais | R$ 1.889,83831 |
| desembolso estimado | R$ 10.091,36931 |

## 4. Bugs da Engine encontrados e corrigidos

### CR-HW-001 — fecho oculto errado para cremonas longas

**Causa:** a seleção procurava substrings. Assim, `1400MM` continha `400MM` e
`1600MM` continha `600MM`, selecionando `FEC2`.

**Correção:** comparação exata dos comprimentos normalizados. Cremona de
1.200/1.400/1.600 mm agora usa `FEC3`.

**Impacto anterior:** nos modos com fecho oculto, o BOM podia usar o fecho de
600 mm (`FEC2`, R$ 28,16) no lugar do fecho de 1.200 mm (`FEC3`, R$ 59,00),
subestimando R$ 30,84 por fecho. Em 4/6 folhas, a quantidade é 2 e a diferença
podia chegar a R$ 61,68 por esquadria.

### CR-VAL-001 — ferragem desconhecida gerava orçamento parcial

**Causa:** cremona ou roldana inexistente gerava warning, removia o componente e
continuava o cálculo.

**Correção:** fechamento, cremona e roldana são validados contra os catálogos.
A Engine gera `ValueError` e a API responde 422, evitando suborçamento silencioso.

### CR-VAL-002 — valores não finitos e vidro de 0 mm

**Causa:** `NaN`/infinito passavam pela validação e medidas negativas de vidro
eram truncadas para zero pelos helpers.

**Correção:** dimensões e comprimento de barra devem ser finitos e positivos;
largura/altura de vidro não físicas agora interrompem o cálculo.

### CR-WARN-001 — falso positivo DE5013

**Causa:** o alerta legado disparava para qualquer linha DE5013 com 4 cortes e 2
barras, inclusive o controle unitário de 4 folhas que o Excel calcula certo.

**Correção:** o alerta exige a assinatura histórica completa: quatro cortes de
1902 mm, duas barras e origem em mais de um item. O plano físico nunca foi
reduzido: continua usando duas barras.

Nenhum preço, folga ou fórmula válida foi alterado. O golden permaneceu
R$ 8.317,53971 após as correções.

## 5. Divergências e bugs conhecidos do Excel

### PAR2 negativo — bug comprovado do Excel

Sem bandeiras, `AA2=0` e `AB2=0`, mas `D38` e `D44` retornam `-50`. A parcela:

`((0 - 50 + 0 - 50) / 1000) × 2 × 4 = -0,8 parafuso`

Com `PAR2 = R$ 0,10/un.`, o Excel reduz artificialmente R$ 0,08 por item. Nos
quatro itens do golden, a diferença é R$ 0,32. Classificação: **bug comprovado
do Excel; não reproduzir**.

### DE5013 consolidado — bug comprovado do Excel

No pedido histórico com dois itens DESIGN de 2 folhas, cada item gera 2 cortes
de 1902 mm. O pedido soma 4 cortes = 7608 mm e exige 2 barras de 5900 mm. A
Engine usa 2 e o Excel histórico registrou 1. Classificação: **bug comprovado do
Excel na consolidação entre itens**.

Controle negativo: DESIGN 2000×2000, 4 folhas, qtd 1 também gera 4 cortes de
1902 mm, mas tanto Excel quanto Engine retornam 2 barras. Esse caso não recebe
mais o alerta legado.

### DT-CR-003 e DT-CR-004 — compatibilidade sem impacto atual

- DESIGN consulta hoje o transpasse PRIME em parte da largura;
- DESIGN de 6 folhas consulta o fechamento central PRIME;
- PRIME e DESIGN valem 8 mm em ambos os pares de parâmetros, logo não existe
  divergência numérica atual;
- os warnings foram preservados para detectar uma futura separação de valores.

### Diferença de configuração identificada

O teste histórico de compra tinha dois itens DESIGN. O golden técnico atual tem
apenas um DESIGN e usa PRIME no quarto item. Misturar os dois pedidos explica
diferenças de consumo, barras e o aparecimento/ausência do alerta DE5013; não é
bug de fórmula.

## 6. Estado das funcionalidades do CR

| Funcionalidade | Estado | Observação |
|---|---|---|
| geometria base 2/3/4/6 folhas | **IMPLEMENTADO** | validado pelas regras conhecidas e golden disponível |
| BOM/custos do recorte simples | **IMPLEMENTADO** | perfis, baguetes, vidro, vedações, acessórios, ferragens e acabamentos |
| aplicação independente | **IMPLEMENTADO** | JANELA/PORTA controla acabamento sem inferência pelo perfil |
| compra/plano de corte por pedido | **IMPLEMENTADO** | FFD consolida todos os itens e respeita 5900 mm |
| tela simples | **PARCIAL** | componentes existem; combinações com regras ausentes não podem ser validadas |
| persiana | **PARCIAL** | desconta caixa de 200 mm; kit/material/custo não entram no BOM |
| reforço básico de marco/folha | **IMPLEMENTADO** | perfis RAG presentes |
| reforço estrutural condicional/bandeiras | **NÃO IMPLEMENTADO** | regra `U2` do legado não foi migrada |
| travessas internas | **NÃO IMPLEMENTADO** | sem entrada, geometria ou BOM |
| bandeira superior | **NÃO IMPLEMENTADO** | sem entrada, geometria ou BOM |
| bandeira inferior | **NÃO IMPLEMENTADO** | sem entrada, geometria ou BOM |
| cotas manuais | **NÃO IMPLEMENTADO** | sem campos/regras |
| tela + travessas/bandeiras | **NÃO IMPLEMENTADO** | depende das regras ausentes |
| múltiplos vãos de vidro por folha | **NÃO IMPLEMENTADO** | Engine repete um único vidro por folha |
| comprimento de barra na Engine | **IMPLEMENTADO** | o plano aceita comprimento técnico configurável; exposição/persistência por empresa pertence à Camada 2 |
| perda de serra/kerf | **NÃO IMPLEMENTADO** | viabilidade atual assume soma nominal dos cortes, sem espessura de corte |

Os itens de infraestrutura SaaS foram deliberadamente excluídos desta tabela:
eles não diminuem a completude matemática da Engine nem bloqueiam a certificação
técnica do CR.

Observação adicional: tela em 3 folhas produz atualmente `1,5` unidade de
malha pelo critério `folhas / 2`. A conta é internamente consistente, mas a
topologia física deve ser conferida no Excel/desenho técnico antes de ser
certificada.

### Checklist do gate técnico

| Critério de liberação da Engine CR | Resultado |
|---|---|
| todas as regras técnicas CR necessárias | **REPROVADO** — há regras não migradas |
| geometria | **PARCIAL** — aprovada no recorte simples, ausente para travessas/bandeiras/subdivisões |
| BOM | **PARCIAL** — aprovada no recorte simples, incompleta para recursos pendentes |
| custos técnicos | **PARCIAL** — aprovados para componentes migrados |
| travessas | **REPROVADO** — não implementadas |
| bandeiras superior/inferior | **REPROVADO** — não implementadas |
| reforço estrutural | **REPROVADO** — regra condicional não migrada |
| tela e combinações | **PARCIAL** — tela simples existe; combinações e 3 folhas não certificadas |
| persiana completa | **REPROVADO** — apenas desconto geométrico de 200 mm |
| vidros subdivididos | **REPROVADO** — não implementados |
| compra de barras/plano de corte | **APROVADO COM PREMISSA** — FFD consolidado, barra configurável, kerf zero |
| regressão completa | **PARCIAL** — forte para o recorte migrado; impossível cobrir regras ausentes |
| inexistência de regra desconhecida capaz de mudar o resultado | **REPROVADO** — `.xlsm` e issue não acessíveis |

Como o gate exige aprovação de todos os critérios, qualquer uma das linhas
reprovadas é suficiente para impedir a liberação das próximas famílias.

## 7. Limites do plano de corte

O FFD foi executado por material sobre o pedido inteiro. Todos os cortes dos 12
casos nominais, do golden, dos casos DE5013 e das 192 configurações ficaram em
barras cuja soma nominal é menor ou igual ao estoque.

Isso prova viabilidade sob a regra atual, mas não prova ótimo matemático global:
FFD é uma heurística. Também não há kerf. Se a produção exigir perda por corte,
ela precisa virar parâmetro da Engine e entrar tanto no encaixe quanto nos testes.

## 8. Recomendação final

**É seguro começar os demais modelos? NÃO.**

Esse resultado decorre **somente da Camada 1**. Não decorre da ausência de
PostgreSQL, autenticação, multiempresa, snapshots, estoque ou qualquer outro
componente da infraestrutura SaaS.

O núcleo simples está suficientemente estável para continuar trabalho de
arquitetura/API que não dependa das regras faltantes, mas a liberação técnica
para novas famílias deve aguardar:

1. disponibilizar o `.xlsm` e a issue de fechamento para inventariar e comparar
   as regras restantes célula a célula;
2. implementar e validar travessas, bandeiras, cotas manuais, reforço estrutural
   e kit completo de persiana;
3. validar especificamente tela de 3 folhas e combinações tela + bandeiras/
   travessas;
4. definir tecnicamente se o plano deve incluir kerf ou registrar formalmente a
   premissa de kerf zero;
5. executar novamente as 34 regressões depois da migração dessas regras.

Promover a Engine para um caminho estável, configurar CI e construir a Camada 2
são recomendações importantes de produto/arquitetura, mas não fazem parte do
gate matemático definido para esta etapa.
