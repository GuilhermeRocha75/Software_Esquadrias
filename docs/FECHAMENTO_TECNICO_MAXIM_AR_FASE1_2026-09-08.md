# Fechamento técnico — Maxim-Ar Fase 1

Data de fechamento: 2026-09-09  
Branch: `feature/maxim-ar-engine-v1`  
Versão: `MX_ENGINE_0.1.0`

## 1. Escopo implementado

Baseline de janela Maxim-Ar de uma folha, orientação horizontal, módulo único,
sem tela, bandeiras, travessas ou reforço estrutural adicional. Foram
implementados os sistemas PRIME 42×63 e DESIGN 60×78, com:

- geometria de marco, folha, baguete e vidro;
- BOM auditável com regra/célula de origem;
- reforços internos de marco e folha;
- acabamentos interno e externo comprovados;
- vidro e seleção de baguete por espessura;
- vedações PRIME e alerta para a omissão DESIGN do legado;
- braços por faixa de altura;
- fecho simples e conjunto maçaneta + cremona;
- acessórios e consumo técnico de parafusos;
- custo por grupo e total;
- compra de barras configurável e plano FFD com `kerf_mm=0`;
- API dedicada, API de pedido misto e configurador Web.

A família não é declarada completa. Variantes adiadas estão na seção 15.

## 2. Regras extraídas do Excel

A extração completa, fórmulas e referências estão em
`docs/ENGENHARIA_REVERSA_MAXIM_AR_V1_2026-09-08.md`. A fonte é o XLSM de SHA-256
`96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`, aba
`MX`, células `A1:AU85`.

Foram encontrados 3.636 casos Maxim-Ar na ORCS; 3.129 são de uma folha, o que
fundamenta o recorte inicial.

## 3. Códigos de materiais

- Perfis: `PR4263`, `DE6058`, `DE6078`.
- Baguetes: `BA2516`, `BA2018`, `BA1816`, `BA1216`, `BA1016`, `BA0716`,
  `BA3518`, `BA3218`.
- Reforços: `RAG - PR4263`, `RAG - DE6058`, `RAG - DE6078`.
- Acabamentos: `AC7012`, `AC3004`.
- Vedações: `ACB606`, `AC0002`.
- Acessórios: `AC0312`, `AC0001`.
- Ferragens: `BRA1`–`BRA10`, `FEC4`, `MAC3`, `CRE17`–`CRE20`, `CON1`,
  `PAR1`, `PAR2`.

## 4. Geometria

- Solda: +5 mm (`PFAB!B1`).
- PRIME: folha = dimensão externa − 44 mm.
- DESIGN: folha = dimensão externa − 64 mm.
- PRIME: baguete = folha − 88 mm; vidro = baguete − 8 mm.
- DESIGN: baguete = folha − 120 mm; vidro = baguete − 8 mm.
- Dimensões nulas, negativas e não finitas geram erro explícito.

## 5. BOM

Cada componente contém grupo, papel técnico, código, descrição, unidade,
dimensões aplicáveis, quantidade unitária, quantidade do pedido, preço, custo
e regra/célula de origem. Quantidades do pedido são escaladas sem alterar o
custo técnico unitário.

## 6. Vidros

O catálogo existente é reutilizado. A espessura seleciona a baguete segundo
as faixas exatas de `MX!B12:B13`. Vidro inexistente, sem espessura ou
incompatível com a faixa do sistema é rejeitado.

## 7. Ferragens

Os braços `BRA1`–`BRA10` são selecionados por sistema e altura final da folha.
Fecho simples usa `FEC4`. O segundo modo comprovado usa `MAC3`, uma cremona
Maxim-Ar escolhida por igualdade normalizada/exata e dois `CON1`. Busca por
substring não é aceita.

## 8. Vedações

No PRIME, foram reproduzidos os perímetros de vidro, folha e marco das linhas
67–69. No DESIGN, o XLSM zera todas as vedações por uma condição restrita ao
perfil PRIME. A Engine preserva o custo zero e emite
`LEGACY-MX-DESIGN-SEALING-OMITTED`; o material correto continua pendente.

## 9. Reforços

O baseline inclui os reforços internos sempre calculados pelo legado para
marco e folha. O reforço estrutural adicional de `MX!32`, dependente de
bandeiras, foi inventariado e adiado.

## 10. Custos

O custo técnico usa consumo real: metros cortados, área de vidro e unidades
de ferragens/acessórios. O custo de aquisição usa barras inteiras e permanece
separado. Snapshots históricos da ORCS não substituem o recálculo do XLSM
atual.

## 11. Plano de corte e compra

Materiais lineares chegam ao FFD homologado do CR sem duplicação de algoritmo.
O comprimento da barra é configurável; o padrão de compatibilidade é 5.900 mm
e `kerf_mm=0`. Um endpoint unificado consolida materiais de pedidos mistos CR
+ Maxim-Ar antes de otimizar.

No golden PRIME 800×800:

- custo técnico: R$ 419,780400;
- consumo técnico dos materiais em barra: R$ 292,794400;
- compra de barras: R$ 510,173000;
- materiais não comprados em barra: R$ 126,986000;
- aquisição estimada: R$ 637,159000;
- `PR4263`: 8 cortes, 6.264 mm, 2 barras;
- `RAG - PR4263`: 8 cortes, 5.520 mm, 1 barra.

## 12. Casos Excel × Engine

| ORCS | Sistema e dimensão | Excel | Engine | Diferença |
| ---: | --- | ---: | ---: | ---: |
| 7 | PRIME 680×690 | 358,177200 | 358,177200 | 0 |
| 11 | DESIGN 550×550 | 378,126020 | 378,126020 | 0 |
| 24 | DESIGN 1150×700 | 645,068520 | 645,068520 | 0 |
| 16942 | PRIME 800×800 | 419,780400 | 419,780400 | 0 |
| 18712 | DESIGN 600×600 | 409,292520 | 409,292520 | 0 |
| 15766 | PRIME 580×590, vidro 8 mm | 359,840840 | 359,840840 | 0 |

Também foi isolado de ORCS 3194 um caso sem bandeira com maçaneta e cremona:
Excel e Engine = R$ 1.074,431820.

## 13. Testes

- Engine CR: 57 aprovados.
- Engine Maxim-Ar: 16 aprovados.
- API: 15 aprovados, sendo 7 de regressão CR e 8 de Maxim-Ar/unificação.
- Falhas: 0.
- Build Web Vite: aprovado, 30 módulos transformados.

## 14. Diferenças e bugs identificados

- `LEGACY-MX-DESIGN-SEALING-OMITTED`: vedações DESIGN zeradas.
- `LEGACY-MX-SEPARATE-MODULE-REINFORCEMENT-TOTAL`: subtotal `I56` não inclui
  reforços das linhas 48–55; não afeta o baseline.
- Colunas R/U possuem rótulos herdados incompatíveis com o uso real na MX.
- Linhas antigas da ORCS guardam preços anteriores; o golden usa o XLSM atual
  recalculado e fixa o hash da fonte.

## 15. Pendências da Fase 2

1. Comprovar/corrigir as vedações do sistema DESIGN.
2. Múltiplas folhas e orientação vertical.
3. Travessas horizontais e verticais, inclusive cotas customizadas.
4. Bandeiras inferior/superior integradas.
5. Módulos separados e decisão sobre o subtotal de reforços do legado.
6. Reforço estrutural adicional.
7. Tela recolhível e sua fórmula de preço composta.
8. Ampliar a matriz de casos por acabamentos quando existirem opções reais.

## 16. API e Web

Endpoints adicionados:

- `GET /api/v1/engine/maxim-ar/options`;
- `POST /api/v1/engine/maxim-ar/calculate`;
- `POST /api/v1/engine/maxim-ar/purchase-plan`;
- `POST /api/v1/purchase-plans/calculate-all` para CR + Maxim-Ar.

A Web oferece modal Maxim-Ar separado e mostra somente opções homologadas.
Nenhuma fórmula técnica foi adicionada ao frontend ou à API.

## Conclusão

**MAXIM-AR FASE 1: APROVADA**

**É seguro iniciar a Fase 2 do Maxim-Ar: SIM**

A aprovação vale somente para o baseline descrito neste documento.
