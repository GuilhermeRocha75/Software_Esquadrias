from __future__ import annotations

import csv
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from esquadrias_engine import (
    LeafSystem, SlidingConfiguration, calculate_sliding, GLASSES,
    CLOSURE_OPTIONS, CREMONA_OPTIONS, ROLLER_OPTIONS, FINISH_OPTIONS
)

SYSTEM_LABELS = {
    "Janela PRIME 42x66": LeafSystem.PRIME_WINDOW_42x66,
    "Porta PRIME 42x88": LeafSystem.PRIME_DOOR_42x88,
    "Porta DESIGN 60x111": LeafSystem.DESIGN_DOOR_60x111,
}

ROLE_LABELS = {
    "FRAME_HORIZONTAL": "Marco horizontal",
    "FRAME_VERTICAL": "Marco vertical",
    "LEAF_HORIZONTAL": "Folha horizontal",
    "LEAF_VERTICAL": "Folha vertical",
    "SCREEN_LEAF_HORIZONTAL": "Folha da tela horizontal",
    "SCREEN_LEAF_VERTICAL": "Folha da tela vertical",
    "INTERLOCK": "Interlock",
    "LEAF_COVER": "Tapa-folha",
    "CENTRAL_CLOSURE": "Fechamento central",
    "ALUMINUM_RAIL": "Trilho de alumínio",
    "DESIGN_Z_PROFILE": "Perfil Z",
    "DESIGN_Z_TRIM": "Arremate Perfil Z",
    "GLAZING_BEAD_HORIZONTAL": "Baguete horizontal",
    "GLAZING_BEAD_VERTICAL": "Baguete vertical",
    "SCREEN_BEAD_HORIZONTAL": "Baguete tela horizontal",
    "SCREEN_BEAD_VERTICAL": "Baguete tela vertical",
    "INTERNAL_FINISH_HORIZONTAL": "Acabamento interno horizontal",
    "INTERNAL_FINISH_VERTICAL": "Acabamento interno vertical",
    "EXTERNAL_FINISH_HORIZONTAL": "Acabamento externo horizontal",
    "EXTERNAL_FINISH_VERTICAL": "Acabamento externo vertical",
    "FRAME_REINFORCEMENT_HORIZONTAL": "Reforço do marco horizontal",
    "FRAME_REINFORCEMENT_VERTICAL": "Reforço do marco vertical",
    "LEAF_REINFORCEMENT_HORIZONTAL": "Reforço da folha horizontal",
    "LEAF_REINFORCEMENT_VERTICAL": "Reforço da folha vertical",
    "GLASS_PANEL": "Vidro",
    "SCREEN_MESH": "Tela mosquiteira",
    "LEAF_RUBBER": "Borracha da folha",
    "SCREEN_RUBBER": "Borracha da tela",
    "LEAF_BRUSH": "Escova da folha",
    "WIND_STOP": "Corta-vento",
    "GLAZING_BLOCK": "Calço de vidro",
    "DRAIN_CAP": "Tapa deságue",
    "OPENING_LIMITER": "Batente limitador",
    "CREMONA": "Cremona",
    "HANDLE_STANDARD": "Maçaneta",
    "HANDLE_HIDDEN": "Maçaneta oculta",
    "HIDDEN_LATCH": "Fecho oculto",
    "ROLLERS": "Roldanas",
    "COUNTER_LATCH": "Contra-fecho",
    "REINFORCEMENT_SCREWS": "Parafusos de reforço",
    "HARDWARE_SCREWS": "Parafusos de ferragem",
}

GEOMETRY_LABELS = {
    "frame_width_final_mm": "Largura final do marco",
    "frame_height_final_mm": "Altura final do marco",
    "frame_width_cut_mm": "Corte horizontal do marco",
    "frame_height_cut_mm": "Corte vertical do marco",
    "leaf_width_final_mm": "Largura final da folha",
    "leaf_height_final_mm": "Altura final da folha",
    "leaf_width_cut_mm": "Corte horizontal da folha",
    "leaf_height_cut_mm": "Corte vertical da folha",
    "baguette_width_mm": "Baguete horizontal",
    "baguette_height_mm": "Baguete vertical",
    "glass_width_mm": "Vidro — largura",
    "glass_height_mm": "Vidro — altura",
}

def parse_number(value: str, field_name: str, integer: bool = False):
    raw = value.strip().replace(" ", "").replace(",", ".")
    if not raw:
        raise ValueError(f"Informe {field_name}.")
    try:
        number = float(raw)
    except ValueError:
        raise ValueError(f"{field_name} inválido: {value!r}")
    if integer:
        if not number.is_integer():
            raise ValueError(f"{field_name} deve ser inteiro.")
        return int(number)
    return number

def money(value: float) -> str:
    txt = f"{value:,.2f}"
    return "R$ " + txt.replace(",", "X").replace(".", ",").replace("X", ".")

class EsquadriasTester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Software Esquadrias — Tester CR v0.2.0")
        self.geometry("1510x900")
        self.minsize(1220, 760)
        self.current_cfg = None
        self.current_result = None
        self._configure_style()
        self._build_ui()
        self._set_defaults()

    def _configure_style(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("SubTitle.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("BigValue.TLabel", font=("Segoe UI", 15, "bold"))
        style.configure("SmallMuted.TLabel", font=("Segoe UI", 9))

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(16, 12, 16, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Software Esquadrias — Tester CR v0.2", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Composição ampliada: PVC + baguetes + reforços + vidro + vedações + acessórios + ferragens",
            style="SubTitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 14))
        left = ttk.Frame(main, padding=4)
        right = ttk.Frame(main, padding=4)
        main.add(left, weight=0)
        main.add(right, weight=1)
        self._build_input_panel(left)
        self._build_result_panel(right)

    def _build_input_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=" Configuração da esquadria ", padding=12)
        frame.grid(row=0, column=0, sticky="new")
        frame.columnconfigure(1, weight=1)

        vars_ = {
            "width": tk.StringVar(), "height": tk.StringVar(), "quantity": tk.StringVar(),
            "leaf_count": tk.StringVar(), "system": tk.StringVar(), "glass": tk.StringVar(),
            "closure": tk.StringVar(), "cremona": tk.StringVar(), "roller": tk.StringVar(),
            "internal": tk.StringVar(), "external": tk.StringVar(),
            "screen": tk.BooleanVar(), "shutter": tk.BooleanVar(),
            "excel_cost": tk.StringVar(), "notes": tk.StringVar(),
        }
        self.v = vars_

        glass_names = sorted([g.description for g in GLASSES.values()])
        finish_names = list(FINISH_OPTIONS.keys())

        controls = [
            ("Largura (mm)", "width", "entry", None),
            ("Altura (mm)", "height", "entry", None),
            ("Quantidade", "quantity", "entry", None),
            ("Nº de folhas", "leaf_count", "combo", ("2","3","4","6")),
            ("Sistema", "system", "combo", tuple(SYSTEM_LABELS.keys())),
            ("Vidro", "glass", "combo", tuple(glass_names)),
            ("Fechamento", "closure", "combo", tuple(CLOSURE_OPTIONS)),
            ("Cremona", "cremona", "combo", tuple(CREMONA_OPTIONS)),
            ("Roldana", "roller", "combo", tuple(ROLLER_OPTIONS)),
            ("Acabamento interno", "internal", "combo", tuple(finish_names)),
            ("Acabamento externo", "external", "combo", tuple(finish_names)),
        ]
        row = 0
        for label, key, kind, values in controls:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if kind == "entry":
                widget = ttk.Entry(frame, textvariable=vars_[key], width=33)
            else:
                widget = ttk.Combobox(
                    frame, textvariable=vars_[key], values=values,
                    state="readonly", width=48
                )
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            row += 1

        ttk.Checkbutton(frame, text="Tela mosquiteira", variable=vars_["screen"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(7,2)
        ); row += 1
        ttk.Checkbutton(frame, text="Persiana (ainda parcial na v0.2)", variable=vars_["shutter"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=2
        ); row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8); row += 1

        ttk.Label(frame, text="Custo esperado Excel (R$)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=vars_["excel_cost"]).grid(row=row, column=1, sticky="ew", pady=4)
        row += 1
        ttk.Label(frame, text="Observação").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=vars_["notes"]).grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(12,3))
        buttons.columnconfigure(0, weight=1); buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="CALCULAR", command=self.calculate).grid(
            row=0, column=0, sticky="ew", padx=(0,4), ipady=5
        )
        ttk.Button(buttons, text="Limpar resultado", command=self.clear_results).grid(
            row=0, column=1, sticky="ew", padx=(4,0), ipady=5
        )

        tests = ttk.LabelFrame(parent, text=" Dataset Dourado ", padding=12)
        tests.grid(row=1, column=0, sticky="new", pady=(12,0))
        tests.columnconfigure(0, weight=1)
        ttk.Button(tests, text="Salvar caso de teste", command=self.save_test_case).grid(
            row=0, column=0, sticky="ew", pady=3
        )
        ttk.Button(tests, text="Exportar resultado JSON", command=self.export_json).grid(
            row=1, column=0, sticky="ew", pady=3
        )
        ttk.Button(tests, text="Abrir pasta dos casos", command=self.open_cases_folder).grid(
            row=2, column=0, sticky="ew", pady=3
        )

    def _build_result_panel(self, parent):
        parent.columnconfigure(0, weight=1); parent.rowconfigure(1, weight=1)

        summary = ttk.Frame(parent)
        summary.grid(row=0, column=0, sticky="ew", pady=(0,10))
        for i in range(4): summary.columnconfigure(i, weight=1)
        self.model_value = tk.StringVar(value="—")
        self.unit_cost_value = tk.StringVar(value="—")
        self.order_cost_value = tk.StringVar(value="—")
        self.diff_value = tk.StringVar(value="—")
        self._card(summary, 0, "Modelo", self.model_value)
        self._card(summary, 1, "Custo / unidade", self.unit_cost_value)
        self._card(summary, 2, "Custo / pedido", self.order_cost_value)
        self._card(summary, 3, "Diferença vs Excel", self.diff_value)

        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, sticky="nsew")
        geom_tab = ttk.Frame(notebook, padding=10)
        bom_tab = ttk.Frame(notebook, padding=8)
        break_tab = ttk.Frame(notebook, padding=10)
        warn_tab = ttk.Frame(notebook, padding=10)
        notebook.add(geom_tab, text="Geometria")
        notebook.add(bom_tab, text="BOM completa")
        notebook.add(break_tab, text="Custos por grupo")
        notebook.add(warn_tab, text="Alertas")

        self.geometry_tree = ttk.Treeview(geom_tab, columns=("campo","valor"), show="headings")
        self.geometry_tree.heading("campo", text="Medida")
        self.geometry_tree.heading("valor", text="Valor")
        self.geometry_tree.column("campo", width=340, anchor="w")
        self.geometry_tree.column("valor", width=180, anchor="e")
        self.geometry_tree.pack(fill="both", expand=True)

        cols = ("category","role","code","desc","measure","qty","unit_price","cost","order_cost")
        bf = ttk.Frame(bom_tab); bf.pack(fill="both", expand=True)
        bf.columnconfigure(0, weight=1); bf.rowconfigure(0, weight=1)
        self.bom_tree = ttk.Treeview(bf, columns=cols, show="headings")
        heads = {
            "category":"Grupo","role":"Componente","code":"Código","desc":"Descrição",
            "measure":"Medida","qty":"Qtd./un.","unit_price":"Preço un.","cost":"Custo/un.",
            "order_cost":"Custo pedido"
        }
        widths = {
            "category":120,"role":160,"code":90,"desc":270,"measure":140,
            "qty":80,"unit_price":95,"cost":100,"order_cost":110
        }
        for c in cols:
            self.bom_tree.heading(c, text=heads[c])
            self.bom_tree.column(c, width=widths[c], anchor="w" if c in ("category","role","desc") else "e")
        y = ttk.Scrollbar(bf, orient="vertical", command=self.bom_tree.yview)
        x = ttk.Scrollbar(bf, orient="horizontal", command=self.bom_tree.xview)
        self.bom_tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.bom_tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")

        self.break_tree = ttk.Treeview(break_tab, columns=("group","cost","pct"), show="headings")
        self.break_tree.heading("group", text="Grupo")
        self.break_tree.heading("cost", text="Custo")
        self.break_tree.heading("pct", text="% do total")
        self.break_tree.column("group", width=280, anchor="w")
        self.break_tree.column("cost", width=160, anchor="e")
        self.break_tree.column("pct", width=130, anchor="e")
        self.break_tree.pack(fill="both", expand=True)

        self.warning_text = tk.Text(warn_tab, wrap="word", font=("Segoe UI",10), state="disabled")
        self.warning_text.pack(fill="both", expand=True)

        footer = ttk.Frame(parent)
        footer.grid(row=2, column=0, sticky="ew", pady=(8,0))
        footer.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Preencha os dados e clique em CALCULAR.")
        self.version_var = tk.StringVar(value="Engine: —")
        ttk.Label(footer, textvariable=self.status_var, style="SmallMuted.TLabel").grid(row=0,column=0,sticky="w")
        ttk.Label(footer, textvariable=self.version_var, style="SmallMuted.TLabel").grid(row=0,column=1,sticky="e")

    def _card(self, parent, col, title, var):
        card = ttk.LabelFrame(parent, text=f" {title} ", padding=8)
        card.grid(row=0,column=col,sticky="nsew",padx=(0 if col==0 else 5,0))
        ttk.Label(card, textvariable=var, style="BigValue.TLabel", anchor="center").pack(fill="both",expand=True)

    def _set_defaults(self):
        self.v["width"].set("2000")
        self.v["height"].set("2000")
        self.v["quantity"].set("1")
        self.v["leaf_count"].set("2")
        self.v["system"].set("Porta PRIME 42x88")
        self.v["glass"].set("04mm FLOAT INCOLOR")
        self.v["closure"].set("MAÇANETA COM CREMONA + FECHO OCULTO")
        self.v["cremona"].set("CREMONA 1 PONTO")
        self.v["roller"].set("ROLDANA 30KG")
        self.v["internal"].set("GUARNIÇÃO DE 70MM")
        self.v["external"].set("BARRA CHATA DE 30MM")
        self.v["screen"].set(False)
        self.v["shutter"].set(False)

    def _build_config(self):
        system_label = self.v["system"].get()
        if system_label not in SYSTEM_LABELS:
            raise ValueError("Selecione o sistema.")
        return SlidingConfiguration(
            width_mm=parse_number(self.v["width"].get(),"largura"),
            height_mm=parse_number(self.v["height"].get(),"altura"),
            quantity=parse_number(self.v["quantity"].get(),"quantidade",integer=True),
            leaf_count=parse_number(self.v["leaf_count"].get(),"número de folhas",integer=True),
            leaf_system=SYSTEM_LABELS[system_label],
            glass_description=self.v["glass"].get(),
            closure_mode=self.v["closure"].get(),
            cremona_base=self.v["cremona"].get(),
            roller_description=self.v["roller"].get(),
            internal_finish=self.v["internal"].get(),
            external_finish=self.v["external"].get(),
            screen_enabled=self.v["screen"].get(),
            shutter_enabled=self.v["shutter"].get(),
        )

    def calculate(self):
        try:
            cfg=self._build_config()
            result=calculate_sliding(cfg)
        except Exception as exc:
            messagebox.showerror("Não foi possível calcular",str(exc),parent=self)
            return
        self.current_cfg=cfg; self.current_result=result
        self._render(cfg,result)

    def _render(self,cfg,result):
        self.model_value.set(result.model_description)
        self.unit_cost_value.set(money(result.unit_cost))
        self.order_cost_value.set(money(result.unit_cost*cfg.quantity))
        self.version_var.set(f"Engine: {result.calculation_version}")

        raw=self.v["excel_cost"].get().strip()
        if raw:
            try:
                expected=parse_number(raw,"custo esperado no Excel")
                diff=result.unit_cost-expected
                pct=(diff/expected*100) if expected else 0
                self.diff_value.set(f"{money(diff)} ({pct:+.3f}%)")
            except Exception:
                self.diff_value.set("Valor Excel inválido")
        else:
            self.diff_value.set("—")

        for tree in (self.geometry_tree,self.bom_tree,self.break_tree):
            for item in tree.get_children(): tree.delete(item)

        for key,value in result.geometry.items():
            txt=f"{value:,.3f} mm".replace(",","X").replace(".",",").replace("X",".")
            self.geometry_tree.insert("", "end", values=(GEOMETRY_LABELS.get(key,key),txt))

        for comp in result.unit_bom:
            if comp.unit=="m":
                measure=f"{comp.length_mm:,.1f} mm".replace(",","X").replace(".",",").replace("X",".")
            elif comp.unit=="m²":
                measure=f"{comp.width_mm:.1f} × {comp.height_mm:.1f} mm"
            else:
                measure="unidade"
            self.bom_tree.insert("", "end", values=(
                comp.category,
                ROLE_LABELS.get(comp.role,comp.role),
                comp.material_code,
                comp.description,
                measure,
                f"{comp.quantity_per_unit:g}",
                money(comp.unit_price),
                money(comp.cost_per_unit_product),
                money(comp.cost_per_unit_product*cfg.quantity),
            ))

        total=result.unit_cost or 1.0
        for group,cost in result.cost_breakdown.items():
            if group=="TOTAL": continue
            self.break_tree.insert("", "end", values=(group,money(cost),f"{cost/total*100:.2f}%"))
        self.break_tree.insert("", "end", values=("TOTAL",money(result.unit_cost),"100,00%"))

        self.warning_text.configure(state="normal")
        self.warning_text.delete("1.0","end")
        if result.warnings:
            for w in result.warnings:
                self.warning_text.insert("end",f"[{w.code}]\n{w.message}\n\n")
        else:
            self.warning_text.insert("end","Nenhum alerta para esta configuração.")
        self.warning_text.configure(state="disabled")
        self.status_var.set(f"Cálculo concluído • {len(result.unit_bom)} itens de BOM • {len(result.warnings)} alerta(s)")

    def clear_results(self):
        self.current_cfg=None; self.current_result=None
        self.v["excel_cost"].set(""); self.v["notes"].set("")
        self.model_value.set("—"); self.unit_cost_value.set("—"); self.order_cost_value.set("—"); self.diff_value.set("—")
        self.version_var.set("Engine: —")
        for tree in (self.geometry_tree,self.bom_tree,self.break_tree):
            for item in tree.get_children(): tree.delete(item)
        self.warning_text.configure(state="normal"); self.warning_text.delete("1.0","end"); self.warning_text.configure(state="disabled")
        self.status_var.set("Resultado limpo. Configuração mantida.")

    def _cases_dir(self):
        p=PROJECT_ROOT/"test_cases"; p.mkdir(parents=True,exist_ok=True); return p

    def save_test_case(self):
        if not self.current_cfg or not self.current_result:
            messagebox.showwarning("Sem cálculo","Calcule antes de salvar.",parent=self); return
        expected=None; diff=None; diff_pct=None
        raw=self.v["excel_cost"].get().strip()
        if raw:
            expected=parse_number(raw,"custo esperado no Excel")
            diff=self.current_result.unit_cost-expected
            diff_pct=(diff/expected*100) if expected else None

        cfg=self.current_cfg; res=self.current_result; now=datetime.now()
        row={
            "timestamp":now.isoformat(timespec="seconds"),
            "calculation_version":res.calculation_version,
            "width_mm":cfg.width_mm,"height_mm":cfg.height_mm,"quantity":cfg.quantity,
            "leaf_count":cfg.leaf_count,"leaf_system":cfg.leaf_system.value,
            "glass_description":cfg.glass_description,
            "closure_mode":cfg.closure_mode,
            "cremona_base":cfg.cremona_base,
            "roller_description":cfg.roller_description,
            "internal_finish":cfg.internal_finish,
            "external_finish":cfg.external_finish,
            "screen_enabled":cfg.screen_enabled,"shutter_enabled":cfg.shutter_enabled,
            "engine_unit_cost":res.unit_cost,
            "excel_expected_unit_cost":"" if expected is None else expected,
            "difference_value":"" if diff is None else diff,
            "difference_pct":"" if diff_pct is None else diff_pct,
            "notes":self.v["notes"].get().strip(),
            "breakdown_json":json.dumps(res.cost_breakdown,ensure_ascii=False),
            "geometry_json":json.dumps(res.geometry,ensure_ascii=False),
            "warnings_json":json.dumps([asdict(x) for x in res.warnings],ensure_ascii=False),
            "bom_json":json.dumps([asdict(x) for x in res.unit_bom],ensure_ascii=False),
        }
        csv_path=self._cases_dir()/"golden_cases_v0_2.csv"
        exists=csv_path.exists()
        with csv_path.open("a",newline="",encoding="utf-8-sig") as f:
            writer=csv.DictWriter(f,fieldnames=list(row.keys()),delimiter=";")
            if not exists: writer.writeheader()
            writer.writerow(row)
        case_id=f"CR_{now.strftime('%Y%m%d_%H%M%S')}_{cfg.leaf_count}F"
        json_path=self._cases_dir()/f"{case_id}.json"
        json_path.write_text(json.dumps({
            "case_id":case_id,"input":{**asdict(cfg),"leaf_system":cfg.leaf_system.value},
            "expected_excel":{"unit_cost":expected},
            "engine_result":{
                "calculation_version":res.calculation_version,
                "unit_cost":res.unit_cost,"cost_breakdown":res.cost_breakdown,
                "geometry":res.geometry,"bom":[asdict(x) for x in res.unit_bom],
                "warnings":[asdict(x) for x in res.warnings],
            },
            "comparison":{"difference_value":diff,"difference_pct":diff_pct},
            "notes":self.v["notes"].get().strip(),
        },ensure_ascii=False,indent=2),encoding="utf-8")
        messagebox.showinfo("Caso salvo",f"Caso salvo em:\n{csv_path.name}\n{json_path.name}",parent=self)

    def export_json(self):
        if not self.current_cfg or not self.current_result:
            messagebox.showwarning("Sem cálculo","Calcule antes de exportar.",parent=self); return
        target=filedialog.asksaveasfilename(parent=self,title="Exportar resultado",defaultextension=".json",
                                           filetypes=[("Arquivo JSON","*.json")],initialfile="resultado_cr_v0_2.json")
        if not target: return
        Path(target).write_text(json.dumps({
            "input":{**asdict(self.current_cfg),"leaf_system":self.current_cfg.leaf_system.value},
            "result":{
                "calculation_version":self.current_result.calculation_version,
                "model_description":self.current_result.model_description,
                "geometry":self.current_result.geometry,
                "unit_cost":self.current_result.unit_cost,
                "cost_breakdown":self.current_result.cost_breakdown,
                "bom":[asdict(x) for x in self.current_result.unit_bom],
                "warnings":[asdict(x) for x in self.current_result.warnings],
            }
        },ensure_ascii=False,indent=2),encoding="utf-8")

    def open_cases_folder(self):
        folder=self._cases_dir()
        try:
            if os.name=="nt": os.startfile(folder)
            elif sys.platform=="darwin": os.system(f'open "{folder}"')
            else: os.system(f'xdg-open "{folder}"')
        except Exception:
            messagebox.showinfo("Pasta",str(folder),parent=self)

if __name__=="__main__":
    EsquadriasTester().mainloop()
