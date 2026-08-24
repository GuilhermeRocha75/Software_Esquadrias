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
