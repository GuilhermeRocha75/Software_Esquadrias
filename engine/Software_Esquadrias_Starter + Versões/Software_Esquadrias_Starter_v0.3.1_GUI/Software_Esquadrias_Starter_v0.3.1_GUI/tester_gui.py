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
    LeafSystem, ApplicationType, SlidingConfiguration, calculate_sliding,
    build_order_purchase_plan, GLASSES, CLOSURE_OPTIONS, CREMONA_OPTIONS,
    ROLLER_OPTIONS, FINISH_OPTIONS
)

SYSTEM_LABELS = {
    "Janela PRIME 42x66": LeafSystem.PRIME_WINDOW_42x66,
    "Porta PRIME 42x88": LeafSystem.PRIME_DOOR_42x88,
    "DESIGN 60x111": LeafSystem.DESIGN_DOOR_60x111,
}
APPLICATION_LABELS = {
    "JANELA": ApplicationType.WINDOW,
    "PORTA": ApplicationType.DOOR,
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
    "leaf_height_cut_mm": "Altura de corte da folha",
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

def fmt_mm(value: float) -> str:
    return f"{value:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

class EsquadriasTester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Software Esquadrias — Tester CR v0.5.0")
        self.geometry("1600x930")
        self.minsize(1280, 780)

        self.current_cfg = None
        self.current_result = None
        self.order_items = []  # [(cfg, result)]

        self._style()
        self._build()
        self._defaults()

    def _style(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("SubTitle.TLabel", font=("Segoe UI", 10))
        style.configure("Big.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Muted.TLabel", font=("Segoe UI", 9))

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(15, 10, 15, 5))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            header, text="Software Esquadrias — Tester CR v0.4",
            style="Title.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Agora separa consumo técnico de compra de barras e otimiza todos os itens do pedido em barras de 5.900 mm.",
            style="SubTitle.TLabel"
        ).pack(anchor="w")

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 12))
        left = ttk.Frame(body, padding=4)
        right = ttk.Frame(body, padding=4)
        body.add(left, weight=0)
        body.add(right, weight=1)

        self._inputs(left)
        self._results(right)

    def _inputs(self, parent):
        box = ttk.LabelFrame(parent, text=" Configuração do item ", padding=10)
        box.grid(row=0, column=0, sticky="new")
        box.columnconfigure(1, weight=1)

        self.v = {
            "width": tk.StringVar(), "height": tk.StringVar(),
            "quantity": tk.StringVar(), "leaf_count": tk.StringVar(),
            "system": tk.StringVar(), "application": tk.StringVar(),
            "glass": tk.StringVar(), "closure": tk.StringVar(),
            "cremona": tk.StringVar(), "roller": tk.StringVar(),
            "internal": tk.StringVar(), "external": tk.StringVar(),
            "screen": tk.BooleanVar(), "shutter": tk.BooleanVar(),
            "excel_item_total": tk.StringVar(),
            "excel_pedp_total": tk.StringVar(),
            "notes": tk.StringVar(),
        }

        glass_names = sorted(g.description for g in GLASSES.values())
        finish_names = list(FINISH_OPTIONS.keys())

        controls = [
            ("Largura (mm)", "width", "entry", None),
            ("Altura (mm)", "height", "entry", None),
            ("Quantidade", "quantity", "entry", None),
            ("Nº de folhas", "leaf_count", "combo", ("2", "3", "4", "6")),
            ("Tipo de folha", "system", "combo", tuple(SYSTEM_LABELS.keys())),
            ("Aplicação", "application", "combo", tuple(APPLICATION_LABELS.keys())),
            ("Vidro", "glass", "combo", tuple(glass_names)),
            ("Fechamento", "closure", "combo", tuple(CLOSURE_OPTIONS)),
            ("Cremona", "cremona", "combo", tuple(CREMONA_OPTIONS)),
            ("Roldana", "roller", "combo", tuple(ROLLER_OPTIONS)),
            ("Acabamento interno", "internal", "combo", tuple(finish_names)),
            ("Acabamento externo", "external", "combo", tuple(finish_names)),
        ]

        row = 0
        for label, key, kind, values in controls:
            ttk.Label(box, text=label).grid(row=row, column=0, sticky="w", pady=3)
            if kind == "entry":
                w = ttk.Entry(box, textvariable=self.v[key], width=36)
            else:
                w = ttk.Combobox(
                    box, textvariable=self.v[key], values=values,
                    state="readonly", width=48
                )
            w.grid(row=row, column=1, sticky="ew", pady=3)
            row += 1

        ttk.Checkbutton(box, text="Tela mosquiteira", variable=self.v["screen"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=2
        ); row += 1
        ttk.Checkbutton(
            box, text="Persiana (ainda parcial)", variable=self.v["shutter"]
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2); row += 1

        ttk.Separator(box).grid(row=row, column=0, columnspan=2, sticky="ew", pady=7); row += 1

        ttk.Label(box, text="TOTAL técnico Excel (opcional)").grid(
            row=row, column=0, sticky="w", pady=3
        )
        ttk.Entry(box, textvariable=self.v["excel_item_total"]).grid(
            row=row, column=1, sticky="ew", pady=3
        ); row += 1

        ttk.Label(box, text="TOTAL PED_P Excel (opcional)").grid(
            row=row, column=0, sticky="w", pady=3
        )
        ttk.Entry(box, textvariable=self.v["excel_pedp_total"]).grid(
            row=row, column=1, sticky="ew", pady=3
        ); row += 1

        buttons = ttk.Frame(box)
        buttons.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 2))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="CALCULAR ITEM", command=self.calculate).grid(
            row=0, column=0, sticky="ew", padx=(0, 4), ipady=4
        )
        ttk.Button(buttons, text="+ ADICIONAR AO PEDIDO", command=self.add_to_order).grid(
            row=0, column=1, sticky="ew", padx=(4, 0), ipady=4
        )

        order_box = ttk.LabelFrame(parent, text=" Pedido de teste ", padding=10)
        order_box.grid(row=1, column=0, sticky="new", pady=(10, 0))
        order_box.columnconfigure(0, weight=1)
        ttk.Label(
            order_box,
            text=(
                "A compra de barras é calculada juntando todos os itens abaixo. "
                "É assim que o PED_P do Excel trabalha."
            ),
            wraplength=360,
            style="Muted.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        ob = ttk.Frame(order_box)
        ob.grid(row=1, column=0, sticky="ew")
        ob.columnconfigure(0, weight=1)
        ob.columnconfigure(1, weight=1)
        ttk.Button(ob, text="Remover item selecionado", command=self.remove_order_item).grid(
            row=0, column=0, sticky="ew", padx=(0, 3)
        )
        ttk.Button(ob, text="Limpar pedido", command=self.clear_order).grid(
            row=0, column=1, sticky="ew", padx=(3, 0)
        )

        export_box = ttk.LabelFrame(parent, text=" Exportações ", padding=10)
        export_box.grid(row=2, column=0, sticky="new", pady=(10, 0))
        export_box.columnconfigure(0, weight=1)
        ttk.Button(export_box, text="Exportar plano de compra CSV", command=self.export_purchase_csv).grid(
            row=0, column=0, sticky="ew", pady=2
        )
        ttk.Button(export_box, text="Exportar pedido JSON", command=self.export_order_json).grid(
            row=1, column=0, sticky="ew", pady=2
        )

    def _results(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        cards = ttk.Frame(parent)
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for i in range(5):
            cards.columnconfigure(i, weight=1)

        self.item_cost_var = tk.StringVar(value="—")
        self.order_technical_var = tk.StringVar(value="R$ 0,00")
        self.bar_purchase_var = tk.StringVar(value="R$ 0,00")
        self.procurement_var = tk.StringVar(value="R$ 0,00")
        self.diff_var = tk.StringVar(value="—")

        self._card(cards, 0, "Item — consumo técnico", self.item_cost_var)
        self._card(cards, 1, "Pedido — consumo técnico", self.order_technical_var)
        self._card(cards, 2, "Barras a comprar", self.bar_purchase_var)
        self._card(cards, 3, "Compra estimada total*", self.procurement_var)
        self._card(cards, 4, "Diferença PED_P", self.diff_var)

        nb = ttk.Notebook(parent)
        nb.grid(row=1, column=0, sticky="nsew")

        geom_tab = ttk.Frame(nb, padding=8)
        bom_tab = ttk.Frame(nb, padding=8)
        order_tab = ttk.Frame(nb, padding=8)
        purchase_tab = ttk.Frame(nb, padding=8)
        cut_tab = ttk.Frame(nb, padding=8)
        warn_tab = ttk.Frame(nb, padding=8)

        nb.add(geom_tab, text="Geometria do item")
        nb.add(bom_tab, text="BOM — consumo")
        nb.add(order_tab, text="Itens do pedido")
        nb.add(purchase_tab, text="Compra de barras")
        nb.add(cut_tab, text="Plano de corte")
        nb.add(warn_tab, text="Informações / Alertas")

        self.geometry_tree = ttk.Treeview(
            geom_tab, columns=("field", "value"), show="headings"
        )
        self.geometry_tree.heading("field", text="Medida")
        self.geometry_tree.heading("value", text="Valor")
        self.geometry_tree.column("field", width=360, anchor="w")
        self.geometry_tree.column("value", width=180, anchor="e")
        geom_tab.rowconfigure(0, weight=1)
        geom_tab.columnconfigure(0, weight=1)
        self.geometry_tree.grid(row=0, column=0, sticky="nsew")

        cols = ("group", "role", "code", "desc", "measure", "qty", "price", "cost")
        self.bom_tree = ttk.Treeview(bom_tab, columns=cols, show="headings")
        labels = {
            "group": "Grupo", "role": "Componente", "code": "Código",
            "desc": "Descrição", "measure": "Medida", "qty": "Qtd. pedido",
            "price": "Preço-base", "cost": "Custo consumido"
        }
        widths = {
            "group": 120, "role": 170, "code": 95, "desc": 280,
            "measure": 150, "qty": 90, "price": 110, "cost": 120
        }
        for c in cols:
            self.bom_tree.heading(c, text=labels[c])
            self.bom_tree.column(c, width=widths[c], anchor="w" if c in ("group","role","desc") else "e")
        self._attach_tree(bom_tab, self.bom_tree, horizontal=True)

        ocols = ("idx", "application", "system", "leaves", "width", "height", "qty", "cost")
        self.order_tree = ttk.Treeview(order_tab, columns=ocols, show="headings")
        olabs = {
            "idx":"Item","application":"Aplicação","system":"Tipo de folha",
            "leaves":"Folhas","width":"Largura","height":"Altura",
            "qty":"Qtd.","cost":"Custo técnico"
        }
        owidth = {
            "idx":55,"application":90,"system":220,"leaves":65,
            "width":95,"height":95,"qty":60,"cost":130
        }
        for c in ocols:
            self.order_tree.heading(c, text=olabs[c])
            self.order_tree.column(c, width=owidth[c], anchor="w" if c=="system" else "center")
        self._attach_tree(order_tab, self.order_tree, horizontal=False)

        pcols = ("code","desc","pieces","consumed","bars","purchased","waste","util","price","buycost")
        self.purchase_tree = ttk.Treeview(purchase_tab, columns=pcols, show="headings")
        plabs = {
            "code":"Código","desc":"Descrição","pieces":"Cortes","consumed":"Consumido (m)",
            "bars":"Barras 5,9m","purchased":"Comprado (m)","waste":"Sobra (m)",
            "util":"Aproveit.","price":"R$/m","buycost":"Custo compra"
        }
        pwidth = {
            "code":100,"desc":280,"pieces":65,"consumed":105,"bars":90,
            "purchased":105,"waste":95,"util":90,"price":85,"buycost":115
        }
        for c in pcols:
            self.purchase_tree.heading(c, text=plabs[c])
            self.purchase_tree.column(c, width=pwidth[c], anchor="w" if c=="desc" else "e")
        self._attach_tree(purchase_tab, self.purchase_tree, horizontal=True)

        ccols = ("code","bar","used","left","cuts")
        self.cut_tree = ttk.Treeview(cut_tab, columns=ccols, show="headings")
        clabs = {
            "code":"Código","bar":"Barra","used":"Usado (mm)",
            "left":"Sobra (mm)","cuts":"Cortes"
        }
        cwidth = {"code":110,"bar":70,"used":110,"left":110,"cuts":680}
        for c in ccols:
            self.cut_tree.heading(c, text=clabs[c])
            self.cut_tree.column(c, width=cwidth[c], anchor="w" if c=="cuts" else "e")
        self._attach_tree(cut_tab, self.cut_tree, horizontal=True)

        self.warning_text = tk.Text(warn_tab, wrap="word", font=("Segoe UI",10), state="disabled")
        warn_tab.rowconfigure(0, weight=1)
        warn_tab.columnconfigure(0, weight=1)
        self.warning_text.grid(row=0, column=0, sticky="nsew")

        footer = ttk.Frame(parent)
        footer.grid(row=2, column=0, sticky="ew", pady=(7, 0))
        footer.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Calcule um item e adicione ao pedido.")
        ttk.Label(footer, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text="* Compra estimada = barras inteiras + demais itens pelo consumo. Rolos/embalagens ainda serão modelados.",
            style="Muted.TLabel"
        ).grid(row=1, column=0, sticky="w")

    def _attach_tree(self, parent, tree, horizontal=True):
        """Anexa Treeview e barras de rolagem sem criar frames vazios.

        A v0.3 criava um Frame expansível que não recebia nenhum conteúdo.
        Esse Frame ocupava espaço acima das tabelas em algumas abas.
        """
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        y = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=y.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")

        if horizontal:
            x = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
            tree.configure(xscrollcommand=x.set)
            x.grid(row=1, column=0, sticky="ew")

    def _card(self, parent, col, title, var):
        box = ttk.LabelFrame(parent, text=f" {title} ", padding=7)
        box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 4, 0))
        ttk.Label(box, textvariable=var, style="Big.TLabel", anchor="center").pack(fill="both", expand=True)

    def _defaults(self):
        self.v["width"].set("2000")
        self.v["height"].set("2000")
        self.v["quantity"].set("1")
        self.v["leaf_count"].set("2")
        self.v["system"].set("DESIGN 60x111")
        self.v["application"].set("JANELA")
        self.v["glass"].set("04mm FLOAT INCOLOR")
        self.v["closure"].set("MAÇANETA COM CREMONA + FECHO OCULTO")
        self.v["cremona"].set("CREMONA 1 PONTO")
        self.v["roller"].set("ROLDANA 30KG")
        self.v["internal"].set("GUARNIÇÃO DE 70MM")
        self.v["external"].set("BARRA CHATA DE 30MM")
        self.v["screen"].set(False)
        self.v["shutter"].set(False)

    def _config(self):
        if self.v["system"].get() not in SYSTEM_LABELS:
            raise ValueError("Selecione o tipo de folha.")
        if self.v["application"].get() not in APPLICATION_LABELS:
            raise ValueError("Selecione a aplicação.")
        return SlidingConfiguration(
            width_mm=parse_number(self.v["width"].get(), "largura"),
            height_mm=parse_number(self.v["height"].get(), "altura"),
            quantity=parse_number(self.v["quantity"].get(), "quantidade", integer=True),
            leaf_count=parse_number(self.v["leaf_count"].get(), "número de folhas", integer=True),
            leaf_system=SYSTEM_LABELS[self.v["system"].get()],
            application=APPLICATION_LABELS[self.v["application"].get()],
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
            cfg = self._config()
            result = calculate_sliding(cfg)
        except Exception as exc:
            messagebox.showerror("Erro de cálculo", str(exc), parent=self)
            return
        self.current_cfg, self.current_result = cfg, result
        self._render_item()
        self.status_var.set("Item calculado. Se estiver correto, clique em + ADICIONAR AO PEDIDO.")

    def add_to_order(self):
        try:
            cfg = self._config()
            result = calculate_sliding(cfg)
        except Exception as exc:
            messagebox.showerror("Erro de cálculo", str(exc), parent=self)
            return
        self.current_cfg, self.current_result = cfg, result
        self.order_items.append((cfg, result))
        self._render_item()
        self._render_order()
        self.status_var.set(f"Item adicionado. Pedido agora tem {len(self.order_items)} item(ns).")

    def remove_order_item(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Pedido", "Selecione um item na aba 'Itens do pedido'.", parent=self)
            return
        idx = int(self.order_tree.item(sel[0], "values")[0]) - 1
        if 0 <= idx < len(self.order_items):
            self.order_items.pop(idx)
        self._render_order()

    def clear_order(self):
        self.order_items.clear()
        self._render_order()
        self.status_var.set("Pedido limpo.")

    def _render_item(self):
        cfg, result = self.current_cfg, self.current_result
        self.item_cost_var.set(money(result.unit_cost * cfg.quantity))

        for tree in (self.geometry_tree, self.bom_tree):
            for item in tree.get_children():
                tree.delete(item)

        for key, value in result.geometry.items():
            self.geometry_tree.insert(
                "", "end", values=(GEOMETRY_LABELS.get(key,key), f"{fmt_mm(value)} mm")
            )

        for comp in result.unit_bom:
            if comp.unit == "m":
                measure = f"{fmt_mm(comp.length_mm)} mm"
            elif comp.unit == "m²":
                measure = f"{fmt_mm(comp.width_mm)} × {fmt_mm(comp.height_mm)} mm"
            else:
                measure = "unidade"
            self.bom_tree.insert("", "end", values=(
                comp.category, ROLE_LABELS.get(comp.role, comp.role),
                comp.material_code, comp.description, measure,
                f"{comp.quantity_order:g}", money(comp.unit_price),
                money(comp.cost_per_unit_product * cfg.quantity),
            ))
        self._render_warnings()

    def _render_order(self):
        for tree in (self.order_tree, self.purchase_tree, self.cut_tree):
            for item in tree.get_children():
                tree.delete(item)

        for idx, (cfg, result) in enumerate(self.order_items, start=1):
            self.order_tree.insert("", "end", values=(
                idx, cfg.application.value, cfg.leaf_system.value,
                cfg.leaf_count, fmt_mm(cfg.width_mm), fmt_mm(cfg.height_mm),
                cfg.quantity, money(result.unit_cost * cfg.quantity)
            ))

        plan = build_order_purchase_plan(self.order_items)
        self.order_technical_var.set(money(plan.technical_total))
        self.bar_purchase_var.set(money(plan.bar_stock_purchase_cost))
        self.procurement_var.set(money(plan.procurement_total_estimate))

        raw = self.v["excel_pedp_total"].get().strip()
        if raw and self.order_items:
            try:
                excel_pedp = parse_number(raw, "TOTAL PED_P Excel")
                diff = plan.bar_stock_purchase_cost - excel_pedp
                pct = (diff / excel_pedp * 100.0) if excel_pedp else 0.0
                self.diff_var.set(f"{money(diff)} ({pct:+.3f}%)")
            except Exception:
                self.diff_var.set("Excel inválido")
        else:
            self.diff_var.set("—")

        for line in plan.lines:
            self.purchase_tree.insert("", "end", values=(
                line.material_code, line.description, line.pieces_count,
                f"{line.consumed_length_mm/1000:.3f}",
                line.bars_required,
                f"{line.purchased_length_mm/1000:.3f}",
                f"{line.waste_length_mm/1000:.3f}",
                f"{line.utilization_pct:.2f}%",
                money(line.unit_price_per_m),
                money(line.purchase_cost),
            ))
            for bar in line.bars:
                cuts = " + ".join(f"{p.length_mm:.1f}" for p in bar.pieces)
                self.cut_tree.insert("", "end", values=(
                    line.material_code, bar.bar_number,
                    f"{bar.used_mm:.1f}", f"{bar.leftover_mm:.1f}", cuts
                ))

        self._render_warnings(plan)

    def _render_warnings(self, plan=None):
        warnings = []
        if self.current_result:
            warnings.extend(self.current_result.warnings)
        if plan:
            warnings.extend(plan.warnings)

        info = []
        legacy = []
        technical = []

        for w in warnings:
            if w.code.startswith("DT-CR-"):
                info.append(w)
            elif w.code.startswith("LEGACY-"):
                legacy.append(w)
            else:
                technical.append(w)

        self.warning_text.configure(state="normal")
        self.warning_text.delete("1.0", "end")

        if not warnings:
            self.warning_text.insert("end", "Nenhum alerta técnico ou informação de compatibilidade.")
        else:
            if info:
                self.warning_text.insert(
                    "end",
                    "INFORMAÇÕES DE COMPATIBILIDADE\n"
                    "Estes itens documentam comportamentos herdados do Excel e não significam, "
                    "por si só, erro no cálculo atual.\n\n"
                )
                for w in info:
                    self.warning_text.insert("end", f"ℹ  [{w.code}]\n{w.message}\n\n")

            if legacy:
                self.warning_text.insert(
                    "end",
                    "DIVERGÊNCIAS / CORREÇÕES DO EXCEL LEGADO\n"
                    "Nestes casos a Engine pode produzir resultado propositalmente diferente "
                    "quando o legado contém uma inconsistência física ou lógica.\n\n"
                )
                for w in legacy:
                    self.warning_text.insert("end", f"⚠  [{w.code}]\n{w.message}\n\n")

            if technical:
                self.warning_text.insert("end", "ALERTAS TÉCNICOS\n\n")
                for w in technical:
                    self.warning_text.insert("end", f"⚠  [{w.code}]\n{w.message}\n\n")

        self.warning_text.configure(state="disabled")

    def export_purchase_csv(self):
        if not self.order_items:
            messagebox.showwarning("Pedido", "Adicione itens ao pedido antes de exportar.", parent=self)
            return
        plan = build_order_purchase_plan(self.order_items)
        target = filedialog.asksaveasfilename(
            parent=self, title="Exportar plano de compra",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="plano_compra_perfis_v0_3.csv",
        )
        if not target:
            return
        fields = [
            "codigo","descricao","quantidade_cortes","consumo_m",
            "barras_5900","comprado_m","sobra_m","aproveitamento_pct",
            "preco_m","custo_consumo","custo_compra"
        ]
        with open(target, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
            w.writeheader()
            for line in plan.lines:
                w.writerow({
                    "codigo": line.material_code,
                    "descricao": line.description,
                    "quantidade_cortes": line.pieces_count,
                    "consumo_m": line.consumed_length_mm / 1000,
                    "barras_5900": line.bars_required,
                    "comprado_m": line.purchased_length_mm / 1000,
                    "sobra_m": line.waste_length_mm / 1000,
                    "aproveitamento_pct": line.utilization_pct,
                    "preco_m": line.unit_price_per_m,
                    "custo_consumo": line.consumption_cost,
                    "custo_compra": line.purchase_cost,
                })
        messagebox.showinfo("Exportado", f"Plano salvo em:\n{target}", parent=self)

    def export_order_json(self):
        if not self.order_items:
            messagebox.showwarning("Pedido", "Adicione itens ao pedido antes de exportar.", parent=self)
            return
        plan = build_order_purchase_plan(self.order_items)
        target = filedialog.asksaveasfilename(
            parent=self, title="Exportar pedido",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="pedido_teste_v0_3.json",
        )
        if not target:
            return
        payload = {
            "engine_version": result.calculation_version,
            "items": [
                {
                    "input": {**asdict(cfg), "leaf_system": cfg.leaf_system.value, "application": cfg.application.value},
                    "technical_total": result.unit_cost * cfg.quantity,
                    "geometry": result.geometry,
                    "bom": [asdict(x) for x in result.unit_bom],
                }
                for cfg, result in self.order_items
            ],
            "purchase_plan": {
                "technical_total": plan.technical_total,
                "bar_stock_consumption_cost": plan.bar_stock_consumption_cost,
                "bar_stock_purchase_cost": plan.bar_stock_purchase_cost,
                "exact_nonbar_cost": plan.exact_nonbar_cost,
                "procurement_total_estimate": plan.procurement_total_estimate,
                "purchase_increment_vs_consumption": plan.purchase_increment_vs_consumption,
                "lines": [
                    {
                        **{k:v for k,v in asdict(line).items() if k != "bars"},
                        "bars": [
                            {
                                "bar_number": bar.bar_number,
                                "used_mm": bar.used_mm,
                                "leftover_mm": bar.leftover_mm,
                                "cuts": [asdict(p) for p in bar.pieces],
                            } for bar in line.bars
                        ]
                    } for line in plan.lines
                ],
                "warnings": [asdict(w) for w in plan.warnings],
            }
        }
        Path(target).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    EsquadriasTester().mainloop()
