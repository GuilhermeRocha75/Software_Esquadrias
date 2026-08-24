-- Software Esquadrias — schema PostgreSQL v0.1
-- Foco: multiempresa + catálogo técnico + versionamento + orçamentos + rastreabilidade da Engine.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE material_unit AS ENUM ('LINEAR_M', 'AREA_M2', 'PIECE', 'KG', 'SERVICE');
CREATE TYPE quotation_status AS ENUM ('DRAFT', 'SENT', 'APPROVED', 'REJECTED', 'EXPIRED', 'CANCELLED');
CREATE TYPE calculation_status AS ENUM ('SUCCESS', 'WARNING', 'ERROR');

CREATE TABLE companies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name text NOT NULL,
    trade_name text,
    document_number text,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    name text NOT NULL,
    email text NOT NULL,
    role text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id, email)
);

CREATE TABLE engineering_systems (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid REFERENCES companies(id), -- NULL = biblioteca global do produto
    code text NOT NULL,
    name text NOT NULL,
    version text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    UNIQUE(company_id, code, version)
);

CREATE TABLE materials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid REFERENCES companies(id), -- NULL = catálogo global
    engineering_system_id uuid REFERENCES engineering_systems(id),
    code text NOT NULL,
    description text NOT NULL,
    category text NOT NULL,
    unit material_unit NOT NULL,
    dim_a_mm numeric(12,4),
    dim_b_mm numeric(12,4),
    dim_c_mm numeric(12,4),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id, code)
);

CREATE TABLE material_prices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    material_id uuid NOT NULL REFERENCES materials(id),
    supplier_name text,
    price numeric(14,4) NOT NULL CHECK (price >= 0),
    valid_from date NOT NULL,
    valid_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);
CREATE INDEX ix_material_prices_lookup ON material_prices(company_id, material_id, valid_from DESC);

CREATE TABLE engineering_parameter_sets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid REFERENCES companies(id),
    engineering_system_id uuid REFERENCES engineering_systems(id),
    code text NOT NULL,
    version text NOT NULL,
    valid_from timestamptz NOT NULL DEFAULT now(),
    active boolean NOT NULL DEFAULT true,
    UNIQUE(company_id, code, version)
);

CREATE TABLE engineering_parameters (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parameter_set_id uuid NOT NULL REFERENCES engineering_parameter_sets(id) ON DELETE CASCADE,
    key text NOT NULL,
    numeric_value numeric(14,6),
    text_value text,
    unit text,
    description text,
    UNIQUE(parameter_set_id, key),
    CHECK (numeric_value IS NOT NULL OR text_value IS NOT NULL)
);

CREATE TABLE product_families (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE,
    name text NOT NULL
);

CREATE TABLE product_topologies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_family_id uuid NOT NULL REFERENCES product_families(id),
    engineering_system_id uuid REFERENCES engineering_systems(id),
    code text NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true,
    UNIQUE(product_family_id, engineering_system_id, code)
);

CREATE TABLE compatibility_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    engineering_system_id uuid REFERENCES engineering_systems(id),
    rule_code text NOT NULL,
    rule_type text NOT NULL,
    priority integer NOT NULL DEFAULT 100,
    conditions jsonb NOT NULL,
    result jsonb NOT NULL,
    active boolean NOT NULL DEFAULT true,
    UNIQUE(engineering_system_id, rule_code)
);

CREATE TABLE customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    name text NOT NULL,
    document_number text,
    phone text,
    email text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_customers_company_name ON customers(company_id, name);

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
    status quotation_status NOT NULL DEFAULT 'DRAFT',
    created_by uuid REFERENCES app_users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(company_id, quotation_number)
);

CREATE TABLE quotation_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    quotation_id uuid NOT NULL REFERENCES quotations(id) ON DELETE CASCADE,
    version_number integer NOT NULL CHECK (version_number > 0),
    commercial_terms jsonb NOT NULL DEFAULT '{}'::jsonb,
    subtotal numeric(14,2),
    discount numeric(14,2),
    total numeric(14,2),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(quotation_id, version_number)
);

CREATE TABLE product_configurations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    product_family_id uuid NOT NULL REFERENCES product_families(id),
    topology_id uuid REFERENCES product_topologies(id),
    config jsonb NOT NULL,
    config_hash text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quotation_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    quotation_version_id uuid NOT NULL REFERENCES quotation_versions(id) ON DELETE CASCADE,
    item_number integer NOT NULL,
    product_configuration_id uuid NOT NULL REFERENCES product_configurations(id),
    quantity numeric(12,3) NOT NULL CHECK (quantity > 0),
    unit_cost numeric(14,4),
    unit_price numeric(14,4),
    total_price numeric(14,2),
    description text,
    UNIQUE(quotation_version_id, item_number)
);

CREATE TABLE calculation_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id),
    quotation_item_id uuid REFERENCES quotation_items(id),
    product_configuration_id uuid NOT NULL REFERENCES product_configurations(id),
    engine_version text NOT NULL,
    parameter_set_id uuid REFERENCES engineering_parameter_sets(id),
    price_reference_at timestamptz NOT NULL DEFAULT now(),
    status calculation_status NOT NULL,
    input_snapshot jsonb NOT NULL,
    output_snapshot jsonb NOT NULL,
    unit_cost numeric(14,4),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_calculation_runs_item ON calculation_runs(quotation_item_id, created_at DESC);

CREATE TABLE bom_components (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_run_id uuid NOT NULL REFERENCES calculation_runs(id) ON DELETE CASCADE,
    material_id uuid REFERENCES materials(id),
    role text NOT NULL,
    unit material_unit NOT NULL,
    length_mm numeric(14,4),
    width_mm numeric(14,4),
    height_mm numeric(14,4),
    quantity_per_unit numeric(14,6) NOT NULL,
    quantity_order numeric(14,6) NOT NULL,
    unit_price numeric(14,4) NOT NULL,
    cost_per_unit_product numeric(14,4) NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ix_bom_components_run ON bom_components(calculation_run_id);
CREATE INDEX ix_bom_components_material ON bom_components(material_id);

CREATE TABLE engineering_warnings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_run_id uuid NOT NULL REFERENCES calculation_runs(id) ON DELETE CASCADE,
    code text NOT NULL,
    severity text NOT NULL DEFAULT 'WARNING',
    message text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Auditoria mínima para mudanças relevantes de cadastro/regra.
CREATE TABLE audit_log (
    id bigserial PRIMARY KEY,
    company_id uuid REFERENCES companies(id),
    user_id uuid REFERENCES app_users(id),
    entity_type text NOT NULL,
    entity_id text NOT NULL,
    action text NOT NULL,
    before_data jsonb,
    after_data jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
