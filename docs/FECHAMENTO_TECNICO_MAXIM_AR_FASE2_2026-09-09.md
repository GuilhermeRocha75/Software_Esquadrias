# Fechamento técnico — Maxim-Ar Fase 2

Data: 2026-09-09

Branch: `feature/maxim-ar-engine-v2`

Base exata: `1aaa99646cf81db6abefa93349e035a67280f260`

Versão: `MX_ENGINE_0.2.0`

## Resultado executivo

A Fase 2 ampliou com segurança a Engine, a API e a Web, mas **não fechou 100%
da família Maxim-Ar**. O XLSM oficial contém fórmulas contraditórias em ramos
de travessas/bandeiras e não contém a definição física da vedação DESIGN.
Conforme o critério de não inventar engenharia, esses ramos foram bloqueados.

Por isso, a entrega de software da v0.2 está testada e utilizável na matriz
abaixo, enquanto o gate técnico integral permanece reprovado. Não é seguro
iniciar a próxima família antes da homologação física pendente ou de uma
decisão formal de escopo que mantenha essas variantes fora do produto.

## Fonte e integridade

- Fonte: `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`.
- Caminho verificado: `C:\Users\rdoug\OneDrive\Desktop\1.2 DELL AMANDA\1.2 DELL AMANDA\SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`.
- SHA-256 confirmado antes da implementação:
  `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`.
- Leitura via Excel 16.0, somente leitura, macros desabilitadas.
- O arquivo não foi alterado, copiado para o repositório nem incluído no Git.
- Abas examinadas: `MX`, `ORCS`, `LISTAPERFIS`, `LISTAFERRA`, `LISTAVIDROS`,
  `LISTADIV` e `PFAB`.

## Inventário ORCS

Foram identificados 3.644 registros pelo discriminador `ORCS!X="MX"`.

| Dimensão | Distribuição observada |
| --- | --- |
| Folhas | 1: 3.136; 2: 374; 3: 91; 4: 33; 5: 2; 6: 3; 7: 2; 8: 3 |
| Sistema | PRIME: 1.221; DESIGN válido: 2.421; duas grafias inválidas |
| Orientação | horizontal: 3.591; vertical: 53 |
| Tela | sem: 3.051; com: 593 |
| Módulo | único: 3.629; separados: 13; vazio: 2 |
| Reforço estrutural | `SEM REFORÇO EXTRUTURAL`: 3.642; vazio: 2; preenchido: 0 |
| Travessas de folha `AF/AG` | 0 casos não nulos |
| Bandeiras | inferior: 483; superior: 163 |

## Escopo implementado

- 1–8 folhas em arranjo horizontal ou vertical, nos sistemas PRIME 42×63 e
  DESIGN 60×78.
- Separadores entre folhas, seus reforços, baguetes, painéis de vidro,
  ferragens e parafusos escalados pelo número de folhas.
- Tela recolhível `TL3` como conjunto comprado, sem decomposição fictícia em
  perfil/malha.
- Bandeiras simples integradas e separadas na matriz coerente.
- Reforços de quadros separados incluídos no BOM e no custo técnico.
- Reforço estrutural `ALUM10238`/`ALUM15338` por bandeira; o recuo de 50 mm é
  aplicado ao `ALUM10238`, conforme `MX!U3`.
- Resultado estruturado de vãos, travessas, bandeiras e painéis de vidro.
- Compra de barras/FFD reutilizada da Engine, com quantidade de pedido,
  `kerf_mm` e consolidação de pedido misto CR + MX.
- API v0.1 mantém as fórmulas exclusivamente na Engine e expõe as limitações
  no endpoint de opções.
- Web com campos condicionais de folhas, orientação, tela, bandeiras, modo de
  módulo e reforço estrutural.

## Casos Excel × Engine

| ORCS | Caso | Excel atual | Engine 0.2 | Delta | Decisão |
| ---: | --- | ---: | ---: | ---: | --- |
| 106 | DESIGN, 2 folhas H, 1400×1000 | 1.074,134120 | 1.074,134120 | 0 | paridade |
| 342 | PRIME, 2 folhas V, 440×1040 | 467,486000 | 466,346560 | -1,139440 | transpasse PRIME corrigido de 8 para 6 mm |
| 162 | PRIME, 1 folha, tela, 500×600 | 518,200400 | 518,200400 | 0 | paridade, `TL3` = 231,00 |
| 343 | DESIGN, bandeiras integradas, 1550×3760 | 2.135,581840 | 2.135,581840 | 0 | paridade |
| 990 | DESIGN, módulos separados, 1000×3300 | 1.514,141160 | 1.573,933160 | +59,792000 | inclui reforços e parafusos omitidos |

O golden `maxim_ar_golden_v0_2.json` fixa esses cinco casos, o hash da fonte,
as geometrias principais e os deltas intencionais. O golden v0.1 permanece no
repositório e seus valores continuam sendo testados.

No caso 990, quantidade 2, o plano de compra resulta em:

- custo técnico do pedido: R$ 3.147,866320;
- compra de barras: R$ 2.837,074000;
- aquisição estimada: R$ 3.736,709200.

## Matriz operacional da v0.2

| Recurso | Liberado | Restrições |
| --- | --- | --- |
| Folhas sem bandeira | 1–8, H/V, PRIME/DESIGN | dimensões físicas positivas |
| Tela | sim | conjunto `TL3`, uma unidade por conjunto MX |
| Bandeira integrada | sim | somente 1 folha; sem travessa vertical |
| Travessa horizontal integrada | parcial | inferior; superior deve espelhar a inferior |
| Módulos separados | sim | somente 1 folha e bandeiras sem travessas |
| Reforço estrutural | sim | exige bandeira; cobertura histórica zero gera alerta |
| Travessas da folha `AF/AG` | não | sem uso ORCS e sem perfil no BOM legado |
| Cotas V:AE | não | nenhuma cota MX real comprovada |

## Bugs corrigidos e compatibilidades

- `LEGACY-MX-PRIME-VERTICAL-DESIGN-OVERLAP-CORRECTED`: usa 6 mm PRIME em vez
  do parâmetro DESIGN de 8 mm referenciado por `MX!D10`.
- `LEGACY-MX-SEPARATE-REINFORCEMENT-SUBTOTAL-CORRECTED`: inclui `I48:I55`,
  omitidos de `MX!I56`.
- `LEGACY-MX-SEPARATE-SCREWS-CORRECTED`: inclui os perfis dos quadros
  separados na taxa de quatro parafusos por metro.
- `LEGACY-MX-DESIGN-SEALING-OMITTED`: preserva zero para não inventar material,
  acompanhado de `PENDING-MX-DESIGN-SEALING-PHYSICAL-DEFINITION`.
- `PENDING-MX-FIXED-GLAZING-BLOCKS`: o Excel fornece calços somente pelas
  folhas móveis; a quantidade física adicional de bandeiras não foi inventada.
- `PENDING-MX-SEPARATE-FIXED-SEALING`: `MX!G67` omite a vedação dos vidros em
  módulos separados; material e perímetro adicionais não foram inventados.

## Pendências que bloqueiam 100%

1. Homologar material, seção, posição e perímetro das vedações do conjunto
   DESIGN (`DE6058`/`DE6078`). A mera existência de `AC0708` no catálogo não é
   prova suficiente.
2. Definir fisicamente as travessas da folha móvel `AF/AG`, inclusive perfil,
   cortes, reforço, divisão dos vidros e significado das cotas V:AE.
3. Corrigir/homologar as bandeiras com múltiplas folhas e travessas verticais:
   as fórmulas atuais ignoram `AH/AJ` e não fecham a largura.
4. Corrigir/homologar as travessas dos módulos separados: o Excel multiplica
   vidros sem dividir sua dimensão e usa campos inferiores no painel superior.
5. Homologar a quantidade de calços dos vidros fixos.
6. Produzir pelo menos um caso físico real de reforço estrutural e confrontar
   `ALUM10238`/`ALUM15338`; hoje a fórmula e o catálogo existem, mas ORCS tem
   zero ocorrências preenchidas.

## Testes e build

Baseline antes das mudanças:

- Engine: 73 aprovados, 181 subtestes;
- API: 15 aprovados;
- Web Vite: aprovado, 30 módulos.

Fechamento da Fase 2:

- Engine total: 85 aprovados, 218 subtestes;
- Maxim-Ar: 28 testes aprovados (16 preservados + 12 novos);
- Matriz combinatória base: 32 configurações (2 sistemas × 2 orientações ×
  8 quantidades de folhas), além das variantes de tela, ferragem, bandeira,
  módulos separados, reforço, quantidade de pedido e cenário de estresse;
- CR: 57 testes preservados;
- API: 20 aprovados, incluindo CR + MX complexo e múltiplos MX distintos;
- Web Vite: aprovado, 30 módulos;
- falhas: 0.

## Decisão de gate

O código da v0.2 está aprovado para a matriz operacional explicitamente
liberada. A Fase 2, cujo objetivo era homologar toda a família, está reprovada
porque restam definições físicas essenciais. O gate da família também está
reprovado e a próxima família não deve ser iniciada.

**MAXIM-AR FASE 2: REPROVADA**

**GATE MAXIM-AR: REPROVADO**

**MAXIM-AR 100% TECNICAMENTE HOMOLOGADO: NÃO**

**É seguro iniciar a próxima família: NÃO**
