# Banco de dados v0.1

O `schema_v0_1.sql` é um rascunho PostgreSQL e já nasce com três decisões importantes:

1. **Multiempresa**: os dados comerciais são isolados por `company_id`.
2. **Material ≠ preço**: atributos técnicos ficam em `materials`; preço histórico fica em `material_prices`.
3. **Cálculo reproduzível**: `calculation_runs` registra versão da engine, conjunto de parâmetros, entrada e saída completas.

Antes da primeira migration real ainda precisamos decidir: autenticação, política de Row Level Security, estratégia de catálogo global vs. catálogo copiado por empresa e política de versionamento das regras de compatibilidade.
