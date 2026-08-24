-- Software Esquadrias — PostgreSQL schema v0.2 (SaaS / multiempresa)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE platform_role AS ENUM ('USER','PLATFORM_ADMIN');
CREATE TYPE company_role AS ENUM ('OWNER','ADMIN','SALES','ENGINEERING','PRODUCTION','FINANCE','VIEWER');
CREATE TYPE subscription_status AS ENUM ('TRIAL','ACTIVE','PAST_DUE','SUSPENDED','CANCELLED');

CREATE TABLE companies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name text NOT NULL,
    trade_name text,
    document_number text,
    slug text UNIQUE,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Usuário global: uma conta pode participar de mais de uma empresa.
CREATE TABLE app_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    email text NOT NULL UNIQUE,
    password_hash text, -- opcional se usarmos provedor externo de autenticação
    platform_role platform_role NOT NULL DEFAULT 'USER',
    active boolean NOT NULL DEFAULT true,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE company_memberships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    role company_role NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id,user_id)
);
CREATE INDEX ix_membership_user ON company_memberships(user_id,active);

CREATE TABLE subscription_plans (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    max_users integer,
    features jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE company_subscriptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    plan_id uuid NOT NULL REFERENCES subscription_plans(id),
    status subscription_status NOT NULL DEFAULT 'TRIAL',
    started_at timestamptz NOT NULL DEFAULT now(),
    trial_ends_at timestamptz,
    current_period_ends_at timestamptz,
    UNIQUE(company_id)
);

CREATE TABLE company_settings (
    company_id uuid PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
    settings jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE material_unit AS ENUM ('LINEAR_M','AREA_M2','PIECE','KG','SERVICE');

-- Catálogo pode ser global (company_id NULL) ou específico da empresa.
CREATE TABLE materials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid REFERENCES companies(id),
    code text NOT NULL,
    description text NOT NULL,
    category text NOT NULL,
    unit material_unit NOT NULL,
    dim_a_mm numeric(12,4),
    dim_b_mm numeric(12,4),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true
);
CREATE UNIQUE INDEX uq_material_global_code ON materials(code) WHERE company_id IS NULL;
CREATE UNIQUE INDEX uq_material_company_code ON materials(company_id,code) WHERE company_id IS NOT NULL;

CREATE TABLE material_prices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    material_id uuid NOT NULL REFERENCES materials(id),
    supplier_name text,
    price numeric(14,4) NOT NULL CHECK(price >= 0),
    valid_from timestamptz NOT NULL DEFAULT now(),
    valid_to timestamptz,
    created_by uuid REFERENCES app_users(id),
    CHECK(valid_to IS NULL OR valid_to >= valid_from)
);
CREATE INDEX ix_price_current ON material_prices(company_id,material_id,valid_from DESC);

CREATE TABLE customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    name text NOT NULL,
    document_number text,
    phone text,
    email text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_customers_tenant ON customers(company_id,name);

CREATE TABLE projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    customer_id uuid NOT NULL REFERENCES customers(id),
    name text NOT NULL,
    address jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quotations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    project_id uuid NOT NULL REFERENCES projects(id),
    quotation_number bigint NOT NULL,
    status text NOT NULL DEFAULT 'DRAFT',
    created_by uuid REFERENCES app_users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id,quotation_number)
);

CREATE TABLE quotation_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    quotation_id uuid NOT NULL REFERENCES quotations(id) ON DELETE CASCADE,
    version_number integer NOT NULL,
    subtotal numeric(14,2),
    discount numeric(14,2),
    total numeric(14,2),
    commercial_terms jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(quotation_id,version_number)
);

CREATE TABLE calculation_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    engine_version text NOT NULL,
    input_snapshot jsonb NOT NULL,
    output_snapshot jsonb NOT NULL,
    unit_cost numeric(14,4),
    order_total_cost numeric(14,4),
    price_reference_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid REFERENCES app_users(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
    id bigserial PRIMARY KEY,
    company_id uuid REFERENCES companies(id),
    user_id uuid REFERENCES app_users(id),
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id text,
    before_data jsonb,
    after_data jsonb,
    ip_address inet,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_company_time ON audit_log(company_id,created_at DESC);

-- Observação: antes de produção, aplicar Row Level Security (RLS) nas tabelas tenant-aware.


-- ===============================================================
-- v0.3 — política de compra, plano de compra e otimização de corte
-- ===============================================================

CREATE TYPE material_costing_mode AS ENUM (
    'EXACT_CONSUMPTION', -- vidro, ferragem, acessórios etc.
    'FULL_STOCK_UNIT'    -- perfis comprados por barra/rolo/chapas inteiras
);

CREATE TABLE company_material_policies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    material_id uuid NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    costing_mode material_costing_mode NOT NULL DEFAULT 'EXACT_CONSUMPTION',
    stock_length_mm numeric(12,3),
    stock_unit_description text,
    allow_remnant_reuse boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id, material_id),
    CHECK(
        costing_mode <> 'FULL_STOCK_UNIT'
        OR stock_length_mm IS NOT NULL
    )
);

CREATE TABLE purchase_plans (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    quotation_version_id uuid REFERENCES quotation_versions(id) ON DELETE CASCADE,
    engine_version text NOT NULL,
    technical_consumption_cost numeric(14,4) NOT NULL DEFAULT 0,
    bar_stock_purchase_cost numeric(14,4) NOT NULL DEFAULT 0,
    procurement_total_estimate numeric(14,4) NOT NULL DEFAULT 0,
    created_by uuid REFERENCES app_users(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE purchase_plan_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_plan_id uuid NOT NULL REFERENCES purchase_plans(id) ON DELETE CASCADE,
    material_id uuid NOT NULL REFERENCES materials(id),
    pieces_count integer NOT NULL DEFAULT 0,
    consumed_length_mm numeric(14,3),
    stock_length_mm numeric(14,3),
    stock_units_required integer,
    purchased_length_mm numeric(14,3),
    waste_length_mm numeric(14,3),
    utilization_pct numeric(8,4),
    price_snapshot numeric(14,4) NOT NULL,
    consumption_cost numeric(14,4) NOT NULL,
    purchase_cost numeric(14,4) NOT NULL
);

CREATE TABLE cut_plan_bars (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_plan_line_id uuid NOT NULL REFERENCES purchase_plan_lines(id) ON DELETE CASCADE,
    bar_number integer NOT NULL,
    stock_length_mm numeric(14,3) NOT NULL,
    used_length_mm numeric(14,3) NOT NULL,
    leftover_length_mm numeric(14,3) NOT NULL,
    UNIQUE(purchase_plan_line_id, bar_number)
);

CREATE TABLE cut_plan_pieces (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cut_plan_bar_id uuid NOT NULL REFERENCES cut_plan_bars(id) ON DELETE CASCADE,
    quotation_item_ref text,
    role text,
    length_mm numeric(14,3) NOT NULL,
    sequence_number integer NOT NULL
);

-- Futuro: tabela de retalhos/sobras reaproveitáveis.
CREATE TABLE material_remnants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    material_id uuid NOT NULL REFERENCES materials(id),
    length_mm numeric(14,3) NOT NULL CHECK(length_mm > 0),
    source_purchase_plan_id uuid REFERENCES purchase_plans(id),
    status text NOT NULL DEFAULT 'AVAILABLE',
    created_at timestamptz NOT NULL DEFAULT now()
);
