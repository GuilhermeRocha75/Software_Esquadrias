from dataclasses import dataclass

@dataclass(frozen=True)
class Material:
    code: str
    description: str
    unit_price: float  # R$/m in this prototype
    dim_a_mm: float | None = None
    dim_b_mm: float | None = None

# Recorte mínimo do catálogo LISTAPERFIS usado pela Engine CR v0.1.
MATERIALS = {
    "PR8852": Material("PR8852", "MARCO 2 TRILHOS COM ABA", 43.57, 52),
    "PR13852": Material("PR13852", "MARCO 3 TRILHOS COM ABA", 76.32, 52),
    "DE16652": Material("DE16652", "MARCO DE CORRER 3 TRILHOS", 97.51, 52),
    "PR4266": Material("PR4266", "FOLHA JANELA DE CORRER 42X66MM", 31.80, 66, 50),
    "PR4288": Material("PR4288", "FOLHA PORTA DE CORRER 42X88MM", 40.70, 88, 72),
    "DE60111": Material("DE60111", "FOLHA PORTA DE CORRER 60X111MM", 68.85, 111, 93),
    "PR4536": Material("PR4536", "INTERLOCK JANELA DE CORRER", 7.47),
    "PR4550": Material("PR4550", "INTERLOCK PORTA DE CORRER", 8.59),
    "DE4109": Material("DE4109", "INTERLOCK FOLHA PORTA DE CORRER", 9.79),
    "DE5013": Material("DE5013", "TAPA FOLHA PORTA DE CORRER", 10.14),
    "AC4222": Material("AC4222", "FECHAMENTO CENTRAL", 14.79),
    "AL16": Material("AL16", "TRILHO PRIME", 4.10),
    "AL19": Material("AL19", "TRILHO DESIGN", 5.10),
}

# PFAB + constantes legadas relevantes neste primeiro recorte.
PARAMETERS = {
    "weld_allowance_mm": 5.0,                  # Excel usa +5 diretamente; PFAB B1=5
    "prime_overlap_mm": 8.0,                  # PFAB B3
    "design_overlap_mm": 8.0,                 # PFAB B4
    "prime_central_meeting_mm": 8.0,          # PFAB B9
    "design_central_meeting_mm": 8.0,         # PFAB B11
    "interlock_clearance_mm": 10.0,           # D32 = D11 - 10
}
