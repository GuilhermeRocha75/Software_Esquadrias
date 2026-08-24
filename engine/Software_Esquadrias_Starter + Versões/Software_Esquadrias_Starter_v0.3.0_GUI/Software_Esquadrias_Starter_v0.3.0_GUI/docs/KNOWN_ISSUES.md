# Pendências herdadas do CR

A Engine v0.1 não “corrige” silenciosamente as fórmulas suspeitas. Ela mantém compatibilidade onde necessário e emite warnings.

- **DT-CR-001** — `O3` usado em D21/G21 em vez de `O2`.
- **DT-CR-002** — typo `EIXOS INDEPENDNETES` em G125.
- **DT-CR-003** — D10 DESIGN usa PFAB B3 (PRIME) em ramos onde existe B4 (DESIGN).
- **DT-CR-004** — 6 folhas DESIGN usa PFAB B9 (PRIME) para fechamento central.
- **DT-CR-005** — constantes mágicas (+5, -10, -40, -50, 200).
- **DT-CR-006** — espessura do vidro inferida de `LEFT(descrição,2)`.
- **DT-CR-007** — número de folhas inferido de `LEFT(texto,1)`.
- **DT-CR-008** — U2 é usado para reforço estrutural, mas U1 não possui cabeçalho.
- **DT-CR-009** — AN2 usa AD2 na descrição do modelo embora AD1 esteja rotulado Cota J.
- **DT-CR-010** — slots fixos Vidro 1..9 / Tela 1..9.
- **DT-CR-011** — regras comparam descrições humanas de materiais.
- **DT-CR-012** — preço e material técnico estão acoplados nas listas operacionais.
