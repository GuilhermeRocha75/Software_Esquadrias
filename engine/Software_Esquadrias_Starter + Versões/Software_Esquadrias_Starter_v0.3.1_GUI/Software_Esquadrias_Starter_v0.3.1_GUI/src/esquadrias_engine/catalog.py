from dataclasses import dataclass
import re
import unicodedata

@dataclass(frozen=True)
class Material:
    code: str
    description: str
    unit_price: float
    unit: str
    dim_a_mm: float | None = None
    dim_b_mm: float | None = None

@dataclass(frozen=True)
class Glass:
    code: str
    description: str
    unit_price: float
    thickness_mm: float | None

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().strip().split())

# Materiais técnicos utilizados pela Engine CR v0.5.
MATERIALS = {
    # Perfis principais
    "PR8852": Material("PR8852", "MARCO 2 TRILHOS COM ABA", 43.57, "m", 52),
    "PR13852": Material("PR13852", "MARCO 3 TRILHOS COM ABA", 76.32, "m", 52),
    "DE16652": Material("DE16652", "MARCO DE CORRER 3 TRILHOS", 97.51, "m", 52),
    "PR4266": Material("PR4266", "FOLHA JANELA DE CORRER 42X66MM", 31.80, "m", 66, 50),
    "PR4288": Material("PR4288", "FOLHA PORTA DE CORRER 42X88MM", 40.70, "m", 88, 72),
    "DE60111": Material("DE60111", "FOLHA PORTA DE CORRER 60X111MM", 68.85, "m", 111, 93),
    "PR4536": Material("PR4536", "INTERLOCK JANELA DE CORRER", 7.47, "m"),
    "PR4550": Material("PR4550", "INTERLOCK PORTA DE CORRER", 8.59, "m"),
    "DE4109": Material("DE4109", "INTERLOCK FOLHA PORTA DE CORRER", 9.79, "m"),
    "DE5013": Material("DE5013", "TAPA FOLHA PORTA DE CORRER", 10.14, "m"),
    "AC4222": Material("AC4222", "FECHAMENTO CENTRAL", 14.79, "m"),
    "AL16": Material("AL16", "TRILHO PRIME", 4.10, "m"),
    "AL17": Material("AL17", "ARREMATE (TRILHO DESIGN)", 8.45, "m"),
    "AL18": Material("AL18", "PERFIL Z (TRILHO DESIGN)", 15.25, "m"),
    "AL19": Material("AL19", "TRILHO DESIGN", 5.10, "m"),
    "PR4263": Material("PR4263", "TRAVESSA (USADA COMO TRAVESSA)", 25.44, "m", 14, 28),
    "DE6072": Material("DE6072", "TRAVESSA / FOLHA JANELA AB. EXT.", 39.14, "m", 18, 36),
    "DE6078": Material("DE6078", "FOLHA JANELA ABERTURA EXTERNA", 45.44, "m", 60, 78),
    "DE6058": Material("DE6058", "MARCO ALTO DE ABRIR", 38.45, "m", 58, 40),
    "ALUM10238": Material("ALUM10238", "PERFIL EXTRUTURAL ALUMINIO 102X50MM", 46.00, "m"),
    "ALUM15338": Material("ALUM15338", "PERFIL EXTRUTURAL ALUMINIO 138X50MM", 46.00, "m"),

    # Baguetes
    "BA2516": Material("BA2516", "BAGUETE (Vidro 4/6mm - 12/18mm)", 10.72, "m"),
    "BA1016": Material("BA1016", "BAGUETE (Vidro 17/22mm - 31mm)", 7.87, "m"),
    "BA1216": Material("BA1216", "BAGUETE (Vidro 16mm)", 8.24, "m"),
    "BA3218": Material("BA3218", "BAGUETE (Tela - 8/10mm)", 12.83, "m"),
    "BA0716": Material("BA0716", "BAGUETE (Vidro 24mm - 34mm)", 7.00, "m"),
    "BA1816": Material("BA1816", "BAGUETE (Vidro 12mm - 22mm)", 9.32, "m"),
    "BA3518": Material("BA3518", "BAGUETE (4/6mm)", 13.25, "m"),
    "BA2018": Material("BA2018", "BAGUETE (Vidro 8/10mm - 19/21mm)", 9.94, "m"),

    # Reforços
    "RAG - PR8852": Material("RAG - PR8852", "REFORÇO - MARCO DE CORRER 2 TRILHOS", 7.00, "m"),
    "RAG - PR13852": Material("RAG - PR13852", "REFORÇO - MARCO DE CORRER 3 TRILHOS", 7.00, "m"),
    "RAG - DE16652": Material("RAG - DE16652", "REFORÇO - MARCO DE CORRER", 7.00, "m"),
    "RAG - PR4288": Material("RAG - PR4288", "REFORÇO - FOLHA PORTA DE CORRER", 13.00, "m"),
    "RAG - PR4266": Material("RAG - PR4266", "REFORÇO - FOLHA JANELA DE CORRER", 7.00, "m"),
    "RAG - DE60111": Material("RAG - DE60111", "REFORÇO - FOLHA PORTA DE CORRER (D)", 25.00, "m"),
    "RAG - PR4263": Material("RAG - PR4263", "REFORÇO - TRAVESSA", 7.00, "m"),
    "RAG - DE6078": Material("RAG - DE6078", "REFORÇO - FOLHA JANELA", 10.00, "m"),
    "RAG - DE6072": Material("RAG - DE6072", "REFORÇO - TRAVESSA / FOLHA JANELA", 7.00, "m"),
    "RAG - DE6058": Material("RAG - DE6058", "REFORÇO - MARCO ALTO DE ABRIR", 8.00, "m"),

    # Acabamentos
    "AC7012": Material("AC7012", "GUARNIÇÃO DE 70MM", 14.63, "m"),
    "AC3004": Material("AC3004", "BARRA CHATA DE 30MM", 3.24, "m"),

    # Vedações e acessórios
    "ACB606": Material("ACB606", "BORRACHA PRIME 6X6", 1.80, "m"),
    "AC0002": Material("AC0002", "BORRACHA MAXIM-AR", 1.60, "m"),
    "AC0708": Material("AC0708", "BORRACHA DESIGN 7X8", 1.80, "m"),
    "ACE606": Material("ACE606", "ESCOVA PRIME 6X6", 0.50, "m"),
    "AC0710": Material("AC0710", "ESCOVA DESIGN 7X10", 0.60, "m"),
    "AC0012": Material("AC0012", "VEDA VENTO PRIME - 12MM", 1.00, "un"),
    "AC0009": Material("AC0009", "VEDA VENTO DESIGN - 9MM", 1.00, "un"),
    "AC0312": Material("AC0312", "CALCO DE VIDRO 3X12", 0.35, "un"),
    "AC0001": Material("AC0001", "TAPA DESAGUE", 1.00, "un"),
    "375441": Material("375441", "LIMITADOR DE ABERTURA", 3.45, "un"),

    # Persiana — LISTAPERFIS!A65:F86 e LISTAFERRA!A48:C49.
    "321040": Material("321040", "CAIXA DE PERSIANA 200MM", 102.93, "m", 200),
    "327201": Material("327201", "GUIA LATERAL", 40.00, "m", 32),
    "327204": Material("327204", "GUIA CENTRAL", 83.03, "m", 30),
    "327019": Material("327019", "PROLONGADOR DE GUIA", 20.00, "m"),
    "326015_F": Material("326015_F", "TALA DE PVC 40MM", 5.00, "m", 40),
    "311712": Material("311712", "TERMINAL DE ALUMINIO", 15.00, "m"),
    "375021": Material("375021", "EIXO DE 60MM", 26.67, "m"),
    "373128": Material("373128", "CONVITE PARA GUIAS LATERAIS (PAR)", 9.44, "un"),
    "370141": Material("370141", "TAMPA LATERAL PARA MOTOR", 44.99, "un"),
    "371553": Material("371553", "PLACA LATERAL PARA MOTOR", 22.32, "un"),
    "370113": Material("370113", "TAMPA LATERAL PARA POLIA/PONTEIRA", 44.95, "un"),
    "371127": Material("371127", "PLACA CENTRAL (EIXOS INDEPENDENTES)", 78.27, "un"),
    "371143": Material("371143", "PLACA CENTRAL (EIXO ÚNICO)", 48.43, "un"),
    "371513_2": Material("371513_2", "PLACA DE CONTENÇÃO (PONTEIRA)", 7.10, "un"),
    "371513_4": Material("371513_4", "PLACA DE CONTENÇÃO (POLIA)", 6.37, "un"),
    "375110": Material("375110", "POLIA", 9.19, "un"),
    "375339": Material("375339", "RECOLHEDOR EMBUTIDO", 45.00, "un"),
    "375678": Material("375678", "ENGATE DA 1ª TALA", 7.69, "un"),
    "375415": Material("375415", "PASSADOR FRONTAL", 4.00, "un"),
    "375213": Material("375213", "PONTEIRA EIXO DE 40MM", 9.00, "un"),
    "375234": Material("375234", "ADAPTADOR DE PONTEIRA 40/60MM", 10.45, "un"),
    "MOT1": Material("MOT1", "MOTOR DE PERSIANA CONTROLE REMOTO", 500.00, "un"),
    "MOT2": Material("MOT2", "MOTOR DE PERSIANA BOTOEIRA", 250.00, "un"),

    # Tela
    "TL1": Material("TL1", "TELA MOSQUITEIRA (TECIDO)", 12.43, "m²"),
    "TL2": Material("TL2", "BORRACHA PARA TELA DE CORRER", 2.00, "m"),

    # Ferragens fixas
    "MAC1": Material("MAC1", "MACANETA STANDARD", 11.00, "un"),
    "MAC2": Material("MAC2", "MAÇANETA DE EMBUTIR CORRER", 14.95, "un"),
    "FEC1": Material("FEC1", "FECHO OCULTO 1 PONTO", 13.00, "un"),
    "FEC2": Material("FEC2", "FECHO OCULTO 2 PONTOS 600mm", 28.16, "un"),
    "FEC3": Material("FEC3", "FECHO OCULTO 2 PONTOS 1200mm", 59.00, "un"),
    "CON1": Material("CON1", "CONTRA FECHO STANDARD", 5.40, "un"),
    "PAR1": Material("PAR1", "PARAFUSOS DE FERRAGEM", 0.15, "un"),
    "PAR2": Material("PAR2", "PARAFUSOS DE REFORÇO", 0.10, "un"),
}

PARAMETERS = {
    "weld_allowance_mm": 5.0,
    "prime_overlap_mm": 8.0,
    "design_overlap_mm": 8.0,
    "prime_central_meeting_mm": 8.0,
    "design_central_meeting_mm": 8.0,
    "glass_clearance_mm": 8.0,
    "interlock_clearance_mm": 10.0,
    "internal_finish_extra_mm": 140.0,
    "external_finish_extra_mm": 60.0,
    "shutter_box_height_mm": 200.0,
    "shutter_side_guide_width_mm": 32.0,
    "shutter_central_guide_width_mm": 30.0,
    "shutter_slat_height_mm": 40.0,
    "shutter_slat_clearance_mm": 10.0,
    "shutter_box_end_clearance_mm": 15.0,
    "shutter_shaft_clearance_mm": 40.0,
    "structural_reinforcement_panel_clearance_mm": 50.0,
    "reinforcement_fastener_rate_per_meter": 4.0,
    "kerf_mm": 0.0,
}

STRUCTURAL_REINFORCEMENT_CODES = {"ALUM10238", "ALUM15338"}

GLASS_ROWS = [{'description': '04mm FLOAT VERDE', 'code': '4FV', 'price': 110.0, 'thickness_mm': 4}, {'description': '04mm FLOAT FUMÊ', 'code': '4FF', 'price': 110.0, 'thickness_mm': 4}, {'description': '04mm FLOAT INCOLOR', 'code': '4FI', 'price': 75.0, 'thickness_mm': 4}, {'description': '04mm MINI BOREAL', 'code': '4MB', 'price': 115.0, 'thickness_mm': 4}, {'description': '04mm CANELADO', 'code': '4C', 'price': 180.0, 'thickness_mm': 4}, {'description': '04mm SEM VIDRO', 'code': '0', 'price': 0.0, 'thickness_mm': 4}, {'description': '05mm FLOAT VERDE', 'code': '5FV', 'price': 120.0, 'thickness_mm': 5}, {'description': '05mm FLOAT FUMÊ', 'code': '5FF', 'price': 120.0, 'thickness_mm': 5}, {'description': '05mm TEMPERADO INCOLOR', 'code': '5TI', 'price': 110.0, 'thickness_mm': 5}, {'description': '05mm FLOAT INCOLOR', 'code': '5FI', 'price': 100.0, 'thickness_mm': 5}, {'description': '10mm TEMPERADO/LAMINADO INCOLOR', 'code': '10TLI', 'price': 450.0, 'thickness_mm': 10}, {'description': '06mm FLOAT FUMÊ', 'code': '6FF', 'price': 155.0, 'thickness_mm': 6}, {'description': '06mm FLOAT INCOLOR', 'code': '6FI', 'price': 115.0, 'thickness_mm': 6}, {'description': '06mm LAMINADO MINIBOREAL', 'code': '6LMB', 'price': 335.0, 'thickness_mm': 6}, {'description': '06mm LAMINADO INCOLOR', 'code': '6LI', 'price': 200.0, 'thickness_mm': 6}, {'description': '06mm LAMINADO FUMÊ', 'code': '6LF', 'price': 265.0, 'thickness_mm': 6}, {'description': '06mm LAMINADO OPACO', 'code': '6LL', 'price': 332.0, 'thickness_mm': 6}, {'description': '06mm LAMINADO REFLETIVO PRATA', 'code': '6LRP', 'price': 260.0, 'thickness_mm': 6}, {'description': '06mm TEMPERADO FUMÊ', 'code': '6TF', 'price': 150.0, 'thickness_mm': 6}, {'description': '06mm TEMPERADO HABITAT REFLETIVO PRATA', 'code': '6THRP', 'price': 260.0, 'thickness_mm': 6}, {'description': '06mm TEMPERADO INCOLOR', 'code': '6TI', 'price': 125.0, 'thickness_mm': 6}, {'description': '06mm TEMPERADO REFLETIVO CHAMPANHE - VB', 'code': '6TRC', 'price': 290.0, 'thickness_mm': 6}, {'description': '06mm TEMPERADO VERDE VB', 'code': '6mmv', 'price': 150.0, 'thickness_mm': 6}, {'description': '08mm FLOAT FUMÊ', 'code': '8FF', 'price': 240.0, 'thickness_mm': 8}, {'description': '08mm FLOAT INCOLOR', 'code': '8FI', 'price': 155.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO/LAMINADO INCOLOR', 'code': '8LT4+4', 'price': 380.0, 'thickness_mm': 8}, {'description': '08MM LAMINADO HABITAT INCOLOR', 'code': '8MML', 'price': 280.0, 'thickness_mm': 8}, {'description': '08mm LAMINADO INCOLOR', 'code': '8LI', 'price': 245.0, 'thickness_mm': 8}, {'description': '08mm LAMINADO FUMÊ', 'code': '8LF', 'price': 345.0, 'thickness_mm': 8}, {'description': '08mm LAMINADO LEITOSO OPACO VB', 'code': '8LL', 'price': 330.0, 'thickness_mm': 8}, {'description': '08mm LAMINADO MINI BOREAL', 'code': '8LMB', 'price': 400.0, 'thickness_mm': 8}, {'description': '08mm LAMINADO REFLETIVO CHAMPANHE -VB', 'code': '8LRC', 'price': 330.0, 'thickness_mm': 8}, {'description': '08mm LAMINADO REFLETIVO PRATA', 'code': '8LRP', 'price': 300.0, 'thickness_mm': 8}, {'description': '08mm MINI BOREAL', 'code': '8MB', 'price': 270.0, 'thickness_mm': 8}, {'description': '08mm MINI BOREAL TEMPERADO', 'code': '8mt', 'price': 297.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO ACIDATO', 'code': '8mmta', 'price': 350.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO FUMÊ', 'code': '8TF', 'price': 185.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO INCOLOR', 'code': '8TI', 'price': 145.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO PONTILHADO VB', 'code': '12TP', 'price': 280.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO REFLETICO CHAMPANHE - VB', 'code': '8TRC', 'price': 325.0, 'thickness_mm': 8}, {'description': '08mm TEMPERADO REFLETIVO PRATA ', 'code': '8TRP', 'price': 325.0, 'thickness_mm': 8}, {'description': '10mm FLOAT INCOLOR', 'code': '10FI', 'price': 180.0, 'thickness_mm': 10}, {'description': '10mm LAMINADO INCOLOR', 'code': '10LI', 'price': 270.0, 'thickness_mm': 10}, {'description': '10mm LAMINADO REFLETIVO CHAMPANHE VB', 'code': '10LRC', 'price': 420.0, 'thickness_mm': 10}, {'description': '10mm TEMPERADO INCOLOR', 'code': '10TI', 'price': 400.0, 'thickness_mm': 10}, {'description': '12mm TEMPERADO INCOLOR', 'code': '12TI', 'price': 280.0, 'thickness_mm': 12}, {'description': '14mm DUPLO FLOAT INCOLOR (4/10/4)', 'code': '14FI(4/10/4)', 'price': 230.0, 'thickness_mm': 14}, {'description': '20mm DUPLO FLOAT INCOLOR (4/10/6)', 'code': '20FI(4/10/6)', 'price': 270.0, 'thickness_mm': 20}, {'description': '20mm DUPLO FLOAT INCOLOR/LAMINADO INCOLOR (4/10/6)', 'code': '20FILI(4/10/6L)', 'price': 355.0, 'thickness_mm': 20}, {'description': '20mm DUPLO FLOAT INCOLOR/MINIBOREAL (6/10/4)', 'code': '20FIMB(6/10/4MB)', 'price': 270.0, 'thickness_mm': 20}, {'description': '20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)', 'code': '20FITI(4/10/6L)', 'price': 250.0, 'thickness_mm': 20}, {'description': '20mm DUPLO LAMINADO INCOLOR/MINIBOREAL (6/10/4)', 'code': '20LIMB(6/10/4MB)', 'price': 395.0, 'thickness_mm': 20}, {'description': '24mm DUPLO TEMPERADO INCOLOR (6/10/8)', 'code': '24TI(6/10/8)', 'price': 350.0, 'thickness_mm': 24}, {'description': '20mm DUPLO TEMPERADO INCOLOR (4/10/6)', 'code': '20TI(4/10/6)', 'price': 310.0, 'thickness_mm': 20}, {'description': '22mm DUPLO TEMPERADO INCOLOR (6/10/6)', 'code': '22TI(6/10/6)', 'price': 330.0, 'thickness_mm': 22}, {'description': '22mm DUPLO FLOAT INCOLOR (6/10/6)', 'code': '22FI(6/10/6)', 'price': 310.0, 'thickness_mm': 22}, {'description': '22mm DUPLO FLOAT INCOLOR/LAMINADO INCOLOR (6/10/6)', 'code': '22FILI(6/10/6)', 'price': 395.0, 'thickness_mm': 22}, {'description': '22mm DUPLO LAMINADO INCOLOR (6/10/6)', 'code': '22LL(6/10/6)', 'price': 480.0, 'thickness_mm': 22}, {'description': '22mm DUPLO TEMPERADO INCOLOR/LAMINADO INCOLOR (6/10/6)', 'code': '22TTL(6/10/6)', 'price': 405.0, 'thickness_mm': 22}, {'description': '24mm DUPLO TEMPERADO INCOLOR/LAMINADO INCOLOR (6/10/8)', 'code': '22TTL(6/10/8)', 'price': 450.0, 'thickness_mm': 24}, {'description': '26mm DUPLO TEMPERADO INCOLOR (8/10/8)', 'code': '26TI6/10/8)', 'price': 370.0, 'thickness_mm': 26}, {'description': '0', 'code': '0', 'price': 0.0, 'thickness_mm': None}]
GLASSES = {
    normalize(row["description"]): Glass(
        row["code"], row["description"], float(row["price"]), row["thickness_mm"]
    )
    for row in GLASS_ROWS
}

HARDWARE_ROWS = [{'description': 'ROLDANA 30KG', 'code': 'ROL1', 'price': 5.0}, {'description': 'ROLDANA 50KG', 'code': 'ROL2', 'price': 9.72}, {'description': 'ROLDANA 80KG', 'code': 'ROL3', 'price': 15.0}, {'description': 'ROLDANA 120KG', 'code': 'ROL4', 'price': 15.0}, {'description': 'ROLDANA 150KG', 'code': 'ROL5', 'price': 35.0}, {'description': 'CREMONA 1 PONTO E:7,5mm', 'code': 'CRE1', 'price': 15.0}, {'description': 'CREMONA 2 PONTOS COMP. 400mm E:7,5mm', 'code': 'CRE2', 'price': 14.35}, {'description': 'CREMONA 2 PONTOS COMP. 600mm E:7,5mm', 'code': 'CRE3', 'price': 21.11}, {'description': 'CREMONA 2 PONTOS COMP. 800mm E:7,5mm', 'code': 'CRE4', 'price': 20.99}, {'description': 'CREMONA 2 PONTOS COMP. 1000mm E:7,5mm', 'code': 'CRE5', 'price': 20.99}, {'description': 'CREMONA 2 PONTOS COMP. 1200mm E:7,5mm', 'code': 'CRE6', 'price': 29.6}, {'description': 'CREMONA 2 PONTOS COMP. 1400mm E:7,5mm', 'code': 'CRE7', 'price': 29.6}, {'description': 'CREMONA 2 PONTOS COMP. 1600mm E:7,5mm', 'code': 'CRE8', 'price': 29.6}, {'description': 'CREMONA 1 PONTO E:15mm', 'code': 'CRE9', 'price': 13.08}, {'description': 'CREMONA 2 PONTOS COMP. 400mm E:15mm', 'code': 'CRE10', 'price': 13.46}, {'description': 'CREMONA 2 PONTOS COMP. 600mm E:15mm', 'code': 'CRE11', 'price': 19.38}, {'description': 'CREMONA 2 PONTOS COMP. 800mm E:15mm', 'code': 'CRE12', 'price': 18.3}, {'description': 'CREMONA 2 PONTOS COMP. 1000mm E:15mm', 'code': 'CRE13', 'price': 18.3}, {'description': 'CREMONA 2 PONTOS COMP. 1200mm E:15mm', 'code': 'CRE14', 'price': 26.91}, {'description': 'CREMONA 2 PONTOS COMP. 1400mm E:15mm', 'code': 'CRE15', 'price': 26.91}, {'description': 'CREMONA 2 PONTOS COMP. 1600mm E:15mm', 'code': 'CRE16', 'price': 26.91}, {'description': 'MACANETA STANDARD', 'code': 'MAC1', 'price': 11.0}, {'description': 'MAÇANETA DE EMBUTIR CORRER', 'code': 'MAC2', 'price': 14.95}, {'description': 'FECHO OCULTO 1 PONTO', 'code': 'FEC1', 'price': 13.0}, {'description': 'FECHO OCULTO 2 PONTOS 600mm', 'code': 'FEC2', 'price': 28.16}, {'description': 'FECHO OCULTO 2 PONTOS 1200mm', 'code': 'FEC3', 'price': 59.0}, {'description': 'MAÇANETA ESTREITA MAXIM-AR', 'code': 'MAC3', 'price': 20.0}, {'description': 'FECHO MAXIM-AR 1 PONTO', 'code': 'FEC4', 'price': 26.0}, {'description': 'CREMONA MAXIM-AR 2 PONTOS COMP. 300mm', 'code': 'CRE17', 'price': 18.3}, {'description': 'CREMONA MAXIM-AR 2 PONTOS COMP. 400mm', 'code': 'CRE18', 'price': 18.66}, {'description': 'CREMONA MAXIM-AR 2 PONTOS COMP. 600mm', 'code': 'CRE19', 'price': 19.64}, {'description': 'CREMONA MAXIM-AR 2 PONTOS COMP. 800mm', 'code': 'CRE20', 'price': 21.98}, {'description': 'CONTRA FECHO STANDARD', 'code': 'CON1', 'price': 5.4}, {'description': 'BRAÇO MAXIM-AR CX 14mm DT10', 'code': 'BRA1', 'price': 25.02}, {'description': 'BRAÇO MAXIM-AR CX 14mm DT12', 'code': 'BRA2', 'price': 26.74}, {'description': 'BRAÇO MAXIM-AR CX 14mm DT16', 'code': 'BRA3', 'price': 29.0}, {'description': 'BRAÇO MAXIM-AR CX 14mm DT20', 'code': 'BRA4', 'price': 40.0}, {'description': 'BRAÇO MAXIM-AR CX 14mm DT24', 'code': 'BRA5', 'price': 40.0}, {'description': 'BRAÇO MAXIM-AR CX 16mm DT10', 'code': 'BRA6', 'price': 60.0}, {'description': 'BRAÇO MAXIM-AR CX 16mm DT12', 'code': 'BRA7', 'price': 60.0}, {'description': 'BRAÇO MAXIM-AR CX 16mm DT16', 'code': 'BRA8', 'price': 85.0}, {'description': 'BRAÇO MAXIM-AR CX 16mm DT20', 'code': 'BRA9', 'price': 85.0}, {'description': 'BRAÇO MAXIM-AR CX 16mm DT24', 'code': 'BRA10', 'price': 95.0}, {'description': 'PARAFUSOS DE FERRAGEM', 'code': 'PAR1', 'price': 0.15}, {'description': 'PARAFUSOS DE REFORÇO', 'code': 'PAR2', 'price': 0.1}, {'description': 'MOTOR DE PERSIANA CONTROLE REMOTO', 'code': 'MOT1', 'price': 500.0}, {'description': 'MOTOR DE PERSIANA BOTOEIRA', 'code': 'MOT2', 'price': 250.0}, {'description': 'FECHADURA MULTIPONTO (GIRO)', 'code': 'FEC5', 'price': 100.0}, {'description': 'MAÇANETA DUPLA (GIRO)', 'code': 'MAC4', 'price': 60.0}, {'description': 'FECHADURA MONOPONTO (GIRO)', 'code': 'FEC6', 'price': 55.0}, {'description': 'MAÇANETA COM CHAVE', 'code': 'MAC5', 'price': 53.0}, {'description': 'CILINDRO 45X45MM', 'code': 'CIL1', 'price': 80.0}, {'description': 'CONTRA-TESTA ', 'code': 'CON2', 'price': 11.0}, {'description': 'CORPO DOBRADIÇA OCULTA', 'code': 'DOB1', 'price': 5.74}, {'description': 'CALÇO DOBRADIÇA OCULTA', 'code': 'DOB2', 'price': 1.2}, {'description': 'DOBRADIÇA 90MM', 'code': 'DOB3', 'price': 51.45}, {'description': 'DOBRADIÇA 105MM', 'code': 'DOB4', 'price': 53.82}, {'description': 'DOBRADIÇA PÉRNIO', 'code': 'DOB5', 'price': 10.07}, {'description': 'FALSO COMPASSO', 'code': 'DOB6', 'price': 18.0}, {'description': 'CORPO DA DOBRADIÇA', 'code': 'DOB7', 'price': 3.14}, {'description': 'CORPO E PINO DOBRADIÇA SUPERIOR', 'code': 'DOB8', 'price': 10.0}, {'description': 'DOBRADIÇA INFERIOR ', 'code': 'DOB9', 'price': 10.0}, {'description': 'SUPORTE DA DOBRADIÇA INFERIOR', 'code': 'DOB10', 'price': 30.0}, {'description': 'CONJUNTO  CAPAS DOBRADIÇA OSCILO', 'code': 'DOB11', 'price': 1.45}, {'description': 'CREMONA OSCILO/GIRO COMP. 400mm E:15mm', 'code': 'CRE21', 'price': 15.0}, {'description': 'CREMONA OSCILO/GIRO COMP. 900mm E:15mm', 'code': 'CRE22', 'price': 17.0}, {'description': 'CREMONA OSCILO/GIRO COMP. 1100mm E:15mm', 'code': 'CRE23', 'price': 18.0}, {'description': 'CREMONA OSCILO/GIRO COMP. 1400mm E:15mm', 'code': 'CRE24', 'price': 20.68}, {'description': 'CREMONA OSCILO/GIRO COMP. 1900mm E:15mm', 'code': 'CRE24', 'price': 25.52}, {'description': 'FECHO UNHA', 'code': 'FEC7', 'price': 5.3}, {'description': 'CONTRA FECHO UNHA', 'code': 'CON3', 'price': 4.01}, {'description': 'PUXADOR 600MM', 'code': 'PUX1', 'price': 100.0}, {'description': 'PUXADOR 800MM', 'code': 'PUX2', 'price': 150.0}, {'description': 'PUXADOR 1000MM', 'code': 'PUX3', 'price': 200.0}, {'description': 'PUXADOR 1200MM', 'code': 'PUX4', 'price': 250.0}, {'description': 'PINO PIVOTANTE', 'code': 'PIN1', 'price': 800.0}, {'description': '0', 'code': '0', 'price': 0.0}]
HARDWARE = {
    normalize(row["description"]): Material(
        row["code"], row["description"], float(row["price"]), "un"
    )
    for row in HARDWARE_ROWS
}

FINISH_OPTIONS = {
    "SEM ACABAMENTO": None,
    "GUARNIÇÃO DE 70MM": "AC7012",
    "BARRA CHATA DE 30MM": "AC3004",
}

CLOSURE_OPTIONS = [
    "MAÇANETA COM CREMONA + FECHO OCULTO",
    "MAÇANETA COM CREMONA + MAÇANETA OCULTA COM CREMONA",
    "MAÇANETA COM CREMONA",
]

CREMONA_OPTIONS = [
    "CREMONA 1 PONTO",
    "CREMONA 2 PONTOS COMP. 400MM",
    "CREMONA 2 PONTOS COMP. 600MM",
    "CREMONA 2 PONTOS COMP. 800MM",
    "CREMONA 2 PONTOS COMP. 1000MM",
    "CREMONA 2 PONTOS COMP. 1200MM",
    "CREMONA 2 PONTOS COMP. 1400MM",
    "CREMONA 2 PONTOS COMP. 1600MM",
]

ROLLER_OPTIONS = [
    "ROLDANA 30KG",
    "ROLDANA 50KG",
    "ROLDANA 80KG",
    "ROLDANA 120KG",
    "ROLDANA 150KG",
]

SHUTTER_MODES = [
    "SEM PERSIANA",
    "MANUAL EM PAINEL ÚNICO",
    "MANUAL EM 2 PAINÉIS COM EIXO ÚNICO",
    "MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES",
    "AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO",
    "AUTOMATIZADA COM BOTOEIRA EM 2 PAINÉIS",
    "AUTOMATIZADA COM BOTOEIRA EM 3 PAINÉIS",
    "AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO",
    "AUTOMATIZADA COM CONTROLE REMOTO EM 2 PAINÉIS",
    "AUTOMATIZADA COM CONTROLE REMOTO EM 3 PAINÉIS",
]
SHUTTER_BOX_OPTIONS = ["CAIXA DE 200MM"]
SHUTTER_SLAT_OPTIONS = ["TALA DE PVC 40MM"]


# Materiais lineares que, no legado, entram no PED_P e são comprados em barras.
# O comprimento padrão atual vem de PFAB!B16 = 5900 mm.
DEFAULT_BAR_LENGTH_MM = 5900.0

BAR_STOCK_CODES = {
    # Marcos / folhas / interlocks / trilhos
    "PR8852", "PR13852", "DE16652",
    "PR4266", "PR4288", "DE60111",
    "PR4536", "PR4550", "DE4109", "DE5013",
    "AC4222", "AL16", "AL17", "AL18", "AL19",
    "PR4263", "DE6072", "DE6078", "DE6058", "ALUM10238", "ALUM15338",

    # Baguetes
    "BA2516", "BA1016", "BA1216", "BA3218",
    "BA0716", "BA1816", "BA3518", "BA2018",

    # Reforços
    "RAG - PR8852", "RAG - PR13852", "RAG - DE16652",
    "RAG - PR4288", "RAG - PR4266", "RAG - DE60111",
    "RAG - PR4263", "RAG - DE6078", "RAG - DE6072", "RAG - DE6058",

    # Acabamentos
    "AC7012", "AC3004",

    # Persiana (linhas de perfil CR!54:60).
    "321040", "327201", "327204", "327019", "326015_F", "311712", "375021",
}
