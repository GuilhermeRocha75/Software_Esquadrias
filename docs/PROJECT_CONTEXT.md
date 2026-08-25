# Software Esquadrias — Contexto do Projeto

## Visão

Transformar o Excel/VBA atual em uma Plataforma de Gestão e Engenharia para Esquadrias, comercializável como SaaS multiempresa.

## Fluxo de negócio alvo

Lead → Cliente → Obra → Orçamento → Engenharia → Venda → Contrato → Medição → Produção → Plano de Corte → Compras → Instalação → Financeiro → Pós-venda.

## Módulo técnico atual

Primeiro módulo: `CR — Correr`.

Entradas principais:
- largura;
- altura;
- quantidade;
- número de folhas;
- tipo de folha;
- aplicação;
- vidro;
- fechamento;
- cremona;
- roldana;
- acabamento interno/externo;
- tela;
- persiana.

Saídas:
- geometria;
- lista de materiais;
- custo por grupo;
- custo técnico;
- plano de compra;
- quantidade de barras;
- sobra;
- plano de corte;
- alertas.

## Validações já concluídas

### Composição técnica

Vidros, ferragens, borrachas, escovas, telas, acessórios e demais grupos foram comparados com o Excel nos testes realizados e os valores ficaram equivalentes no recorte validado.

### Perfis e compra

O Excel usa duas visões distintas:

1. consumo técnico: comprimento efetivamente usado;
2. compra: barras inteiras necessárias.

Comprimento padrão atual no legado: `PFAB!B16 = 5900 mm`.

A Engine v0.3 passou a otimizar os cortes por pedido usando agrupamento por perfil e First Fit Decreasing.

Pedido real de referência validado:
- 349,444 m consumidos;
- 418,900 m comprados;
- 69,456 m de sobra;
- custo de compra das barras: R$ 9.596,881.

### Inconsistência do legado

`DE5013`: 4 cortes × 1902 mm = 7608 mm. O Excel registra 1 barra, porém são necessárias 2 barras de 5900 mm. O novo sistema deve usar 2.

## Interface legado — ações futuras

O painel do Excel possui, entre outras:
- Novo Cliente/Orçamento;
- Buscar Cliente/Orçamento;
- Visualizar Orçamentos;
- Visualizar Orçamento Resumido;
- Inserir Correr;
- Inserir Maxim-Ar;
- Inserir Giro;
- Inserir Fixo;
- Inserir Pivotante;
- Inserir Grade;
- Inserir item manualmente;
- Substituir valor manualmente;
- Definir margem.

Essas ações devem orientar UX e módulos futuros da web, sem acoplar o frontend às fórmulas.

## SaaS / multiempresa

Cada empresa terá seus próprios:
- usuários;
- clientes;
- obras;
- orçamentos;
- materiais/preços;
- parâmetros de compra;
- permissões.

A plataforma terá um papel superior `PLATFORM_ADMIN` para administrar empresas, planos, acessos e módulos.

## Papéis previstos

- PLATFORM_ADMIN
- OWNER
- ADMIN
- SALES
- ENGINEERING
- PRODUCTION
- FINANCE
- VIEWER

## Princípios de dados

- um cliente pode ter várias obras;
- uma obra pode ter vários orçamentos;
- um orçamento possui versões imutáveis;
- cada versão deve preservar snapshots de preços e versão das regras;
- preços são específicos por empresa;
- materiais podem ter políticas de compra distintas por empresa/fornecedor;
- sobras/retalhos poderão virar estoque reaproveitável.

## Próximos passos

1. API FastAPI v0.1 usando a Engine existente;
2. promover Engine validada para caminho estável;
3. autenticação e multiempresa;
4. clientes/obras/orçamentos;
5. primeira interface web;
6. novos módulos técnicos.
