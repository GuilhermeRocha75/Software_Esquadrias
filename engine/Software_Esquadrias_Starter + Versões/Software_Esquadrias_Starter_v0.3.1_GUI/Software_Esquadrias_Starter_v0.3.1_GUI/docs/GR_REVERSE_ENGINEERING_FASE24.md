# GR — Reverse engineering Fase 24

Status: **GR_ENGINE_0.24.0 — INDEPENDÊNCIA ENTRE APLICAÇÃO E TIPO DE FOLHA**

## Confirmação física

Em 30/09/2026, a fabricação confirmou:

- `PORTA` e `JANELA` são classificações de aplicação;
- a aplicação não muda o marco;
- os parâmetros físicos são determinados pelo tipo de folha selecionado;
- as diferenças relevantes ficam na folha e nos componentes associados, como vidro, baguete e auxiliares;
- para a mesma configuração física, trocar somente a aplicação não pode alterar geometria, BOM ou custo.

## Implementação

A Engine v0.24 normaliza internamente a aplicação necessária para percorrer as fórmulas legadas, sempre a partir de `leaf_system`. O valor informado pelo usuário é preservado na descrição comercial do modelo.

Assim, passam a ser aceitas as combinações:

- aplicação `JANELA` com folha de porta 60x104;
- aplicação `PORTA` com folha de janela 60x78.

Em ambas, fechamento, dobradiça, vidro, baguete, bandeiras, tela, persiana e demais regras continuam seguindo a configuração física da folha. A aplicação não libera combinações de ferragens ainda não homologadas.

Quando aplicação e classificação histórica da folha são diferentes, o resultado inclui o aviso `GR-APPLICATION-INDEPENDENT`. Esse aviso é informativo e não altera cálculo.

## Preservação das fórmulas homologadas

Esta fase não reescreve as compensações de corte comprovadas no XLSM:

- folha de porta e seus componentes continuam nas fórmulas homologadas das fases anteriores;
- folha de janela e seus componentes continuam nas fórmulas homologadas das fases anteriores;
- mudar apenas `application` produz exatamente a mesma geometria, BOM, custos e peças de marco.

As diferenças já existentes entre construções físicas de porta e janela não foram tratadas como efeito da aplicação.

## Cobertura histórica

A pendência `application_leaf_system_independence` foi encerrada:

- casos históricos classificados: **47**;
- estado: `RESOLVED_PHYSICAL`;
- evidência: confirmação direta da fabricação em 30/09/2026.

Permanecem abertas cinco frentes:

1. combinações de bandeiras fora da v0.22;
2. compatibilidade entre fechamentos e configurações físicas;
3. fechamentos especiais;
4. vidros ausentes no catálogo;
5. dobradiças pêrnio ou registros inválidos.

O gate continua fechado para plano de compra GR e para integração em `main`.

## Testes adicionados

A suíte da Fase 24 comprova que:

- folha de porta aceita aplicação `JANELA`;
- folha de janela aceita aplicação `PORTA`;
- a troca isolada da aplicação não altera marco, geometria, BOM ou custo;
- a descrição comercial preserva a aplicação escolhida;
- valores fora de `PORTA` e `JANELA` continuam rejeitados;
- o inventário de auditoria cai de seis para cinco pendências.

CR e Maxim-Ar permanecem congelados.
