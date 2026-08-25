# AGENTS.md — Software Esquadrias

## Projeto

Plataforma SaaS de Gestão e Engenharia para empresas de esquadrias.

## Regra principal

Nunca duplicar regras de engenharia na API ou no frontend. Toda fórmula técnica pertence à Engine.

## Arquitetura alvo

- `engine/` — motor técnico e testes de engenharia
- `api/` — FastAPI / contratos HTTP
- `web/` — interface web SaaS
- `database/` — PostgreSQL / schema e migrações
- `docs/` — decisões, regras e contexto do produto

## Estado atual

O módulo validado é `CR — Correr`.

A versão técnica de referência é a Engine v0.3.x, que já calcula:

- geometria;
- BOM;
- custo por grupo;
- custo técnico por consumo;
- plano de compra de barras;
- otimização de barras de 5900 mm;
- plano de corte;
- alertas de compatibilidade com o Excel legado.

## Regras de desenvolvimento

1. Preserve os testes Excel × Engine já validados.
2. Não altere fórmulas sem criar/atualizar um teste de regressão.
3. Separe custo técnico de custo de aquisição.
4. Aplicação (`JANELA`/`PORTA`) é independente do tipo de folha.
5. Comprimento padrão de barra não deve ficar fixo na arquitetura SaaS; deve ser configurável por empresa/material.
6. Toda entidade futura deve considerar `company_id` / isolamento multiempresa.
7. Orçamentos devem possuir versões imutáveis e snapshots de preços/regras.
8. Não armazenar senhas ou segredos no código.
9. Preferir branches e pull requests para alterações relevantes.
10. O Excel legado é referência funcional, mas erros físicos/lógicos comprovados não devem ser copiados cegamente.

## Compatibilidades conhecidas

- `DT-CR-003`: regra DESIGN consulta hoje parâmetro PRIME de transpasse; ambos estão em 8 mm, então não altera o resultado atual.
- `LEGACY-PEDP-DE5013`: o Excel registra 1 barra para 4 cortes de 1902 mm; fisicamente são necessárias 2 barras. A Engine corrige para 2.

## Roadmap imediato

1. estabilizar caminho da Engine (`engine/current` ou pacote equivalente);
2. API v0.1;
3. testes automatizados da API;
4. autenticação e multiempresa;
5. clientes, obras e orçamentos;
6. web app;
7. demais famílias: MX, GR, FX, PV, GD, PCP.
