# Arquitetura Web/SaaS — Software Esquadrias v0.1

## Decisão principal

O `esquadrias_engine` deve permanecer uma biblioteca Python independente de qualquer interface. O Tester Tkinter é apenas um laboratório de validação. A mesma Engine será utilizada futuramente por uma API web.

## Arquitetura alvo

```text
Navegador / celular / tablet
        |
        v
Frontend Web (Next.js/React)
        | HTTPS / JSON
        v
Backend API (FastAPI / Python)
        |
        +--> Esquadrias Engine (CR, MX, GR, FX...)
        |
        +--> PostgreSQL
        |
        +--> Armazenamento de croquis/PDFs
```

## Multiempresa

Cada empresa é um tenant independente. Clientes, usuários, preços, orçamentos, obras e configurações carregam `company_id`.

Um usuário da Empresa A nunca deve enxergar dados da Empresa B.

### Papéis da empresa

- OWNER
- ADMIN
- SALES
- ENGINEERING
- PRODUCTION
- FINANCE
- VIEWER

### Administração da plataforma

Nós teremos contas `PLATFORM_ADMIN` para:

- cadastrar/desativar empresas;
- criar ou bloquear usuários;
- definir plano/assinatura;
- controlar limites de usuários e recursos;
- acompanhar versão da Engine utilizada;
- auditar acessos e alterações.

O administrador da plataforma controla o acesso, mas os dados comerciais de cada cliente devem continuar isolados e auditados.

## Catálogo e preços

A Engine não deve possuir preços comerciais fixos. Ela identifica **o que é necessário para fabricar**. O backend consulta a tabela de preços vigente da empresa e valoriza a BOM.

Isso permite:

- Empresa A pagar R$ 43,57/m pelo PR8852;
- Empresa B pagar R$ 48,10/m pelo mesmo perfil;
- manter o histórico do preço usado em cada orçamento.

## Fluxo de cálculo

```text
Configuração do item
   -> Engine calcula geometria/BOM
   -> API busca preços da empresa
   -> serviço de costing calcula custos
   -> serviço comercial aplica margem/markup
   -> salva snapshot do cálculo
   -> devolve resultado ao navegador
```

## Fases sugeridas

1. Validar CR Engine local contra Excel.
2. Separar catálogo/preços do código.
3. Criar API FastAPI com endpoint `/calculations/sliding`.
4. Subir PostgreSQL e schema multiempresa.
5. Criar autenticação + empresas + memberships.
6. Criar primeiro frontend web de teste.
7. Migrar clientes/orçamentos.
8. Rodar em paralelo Excel + Web na empresa piloto.
9. Abrir o SaaS para outras empresas.
