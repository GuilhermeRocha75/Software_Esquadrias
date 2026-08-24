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

# Permite rodar a interface diretamente da pasta raiz sem instalar o pacote.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from esquadrias_engine import LeafSystem, SlidingConfiguration, calculate_sliding


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
    "INTERLOCK": "Interlock",
    "LEAF_COVER": "Tapa-folha",
    "CENTRAL_CLOSURE": "Fechamento central",
    "ALUMINUM_RAIL": "Trilho de alumínio",
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
}


def parse_number(value: str, field_name: str, integer: bool = False):
    """Aceita 1500, 1500.5 ou 1500,5."""
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
    # Formatação pt-BR sem dependência de locale do Windows.
    txt = f"{value:,.2f}"
    return "R$ " + txt.replace(",", "X").replace(".", ",").replace("X", ".")


class EsquadriasTester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Software Esquadrias — Tester CR v0.1.1")
        self.geometry("1320x820")
        self.minsize(1100, 700)

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
        style.configure("BigValue.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("SmallMuted.TLabel", font=("Segoe UI", 9))

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(16, 12, 16, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Software Esquadrias — Tester CR", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Interface de validação da CR Engine 0.1.0 • cálculos ainda parciais",
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
        frame = ttk.LabelFrame(parent, text=" Dados de entrada ", style="Section.TLabelframe", padding=12)
        frame.grid(row=0, column=0, sticky="new")
        frame.columnconfigure(1, weight=1)

        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.leaf_count_var = tk.StringVar()
        self.system_var = tk.StringVar()
        self.screen_var = tk.BooleanVar()
        self.shutter_var = tk.BooleanVar()
        self.excel_cost_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        row = 0
        ttk.Label(frame, text="Largura (mm)").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.width_var, width=18).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(frame, text="Altura (mm)").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.height_var).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(frame, text="Quantidade").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.quantity_var).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(frame, text="Nº de folhas").grid(row=row, column=0, sticky="w", pady=5)
        leaves = ttk.Combobox(
            frame, textvariable=self.leaf_count_var, values=("2", "3", "4", "6"), state="readonly"
        )
        leaves.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(frame, text="Sistema de folha").grid(row=row, column=0, sticky="w", pady=5)
        systems = ttk.Combobox(
            frame,
            textvariable=self.system_var,
            values=tuple(SYSTEM_LABELS.keys()),
            state="readonly",
            width=25,
        )
        systems.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Checkbutton(frame, text="Tela mosquiteira", variable=self.screen_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(8, 3)
        )
        row += 1
        ttk.Checkbutton(frame, text="Persiana", variable=self.shutter_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        ttk.Label(frame, text="Custo esperado no Excel (R$)").grid(
            row=row, column=0, sticky="w", pady=5
        )
        ttk.Entry(frame, textvariable=self.excel_cost_var).grid(
            row=row, column=1, sticky="ew", pady=5
        )
        row += 1

        ttk.Label(frame, text="Observação").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.notes_var).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        button_row = ttk.Frame(frame)
        button_row.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(14, 3))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        ttk.Button(button_row, text="CALCULAR", command=self.calculate).grid(
            row=0, column=0, sticky="ew", padx=(0, 4), ipady=5
        )
        ttk.Button(button_row, text="Limpar", command=self.clear_results).grid(
            row=0, column=1, sticky="ew", padx=(4, 0), ipady=5
        )

        tests = ttk.LabelFrame(parent, text=" Dataset Dourado ", style="Section.TLabelframe", padding=12)
        tests.grid(row=1, column=0, sticky="new", pady=(12, 0))
        tests.columnconfigure(0, weight=1)

        ttk.Label(
            tests,
            text=(
                "Após conferir o mesmo caso no Excel, informe o custo esperado acima "
                "e salve a comparação."
            ),
            wraplength=300,
            style="SmallMuted.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Button(tests, text="Salvar caso de teste", command=self.save_test_case).grid(
            row=1, column=0, sticky="ew", pady=3
        )
        ttk.Button(tests, text="Exportar resultado JSON", command=self.export_json).grid(
            row=2, column=0, sticky="ew", pady=3
        )
        ttk.Button(tests, text="Abrir pasta dos casos", command=self.open_cases_folder).grid(
            row=3, column=0, sticky="ew", pady=3
        )

        info = ttk.LabelFrame(parent, text=" Escopo desta versão ", style="Section.TLabelframe", padding=12)
        info.grid(row=2, column=0, sticky="new", pady=(12, 0))
        ttk.Label(
            info,
            text=(
                "Implementado: marco, folhas, interlock, fechamento central, "
                "trilho e tapa-folha DESIGN.\n\n"
                "Ainda parcial: tela e persiana.\n"
                "Ainda não implementado: vidro, baguetes, reforços, vedações "
                "e ferragens completas."
            ),
            wraplength=300,
            justify="left",
            style="SmallMuted.TLabel",
        ).grid(row=0, column=0, sticky="w")

    def _build_result_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        summary = ttk.Frame(parent)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for i in range(4):
            summary.columnconfigure(i, weight=1)

        self.model_value = tk.StringVar(value="—")
        self.unit_cost_value = tk.StringVar(value="—")
        self.order_cost_value = tk.StringVar(value="—")
        self.diff_value = tk.StringVar(value="—")

        self._summary_card(summary, 0, "Modelo", self.model_value)
        self._summary_card(summary, 1, "Custo parcial / unidade", self.unit_cost_value)
        self._summary_card(summary, 2, "Custo parcial / pedido", self.order_cost_value)
        self._summary_card(summary, 3, "Diferença vs Excel", self.diff_value)

        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, sticky="nsew")

        geom_tab = ttk.Frame(notebook, padding=12)
        bom_tab = ttk.Frame(notebook, padding=8)
        warn_tab = ttk.Frame(notebook, padding=12)
        notebook.add(geom_tab, text="Geometria")
        notebook.add(bom_tab, text="Materiais / BOM")
        notebook.add(warn_tab, text="Alertas")

        self.geometry_tree = ttk.Treeview(
            geom_tab, columns=("campo", "valor"), show="headings", height=12
        )
        self.geometry_tree.heading("campo", text="Medida")
        self.geometry_tree.heading("valor", text="Valor")
        self.geometry_tree.column("campo", width=330, anchor="w")
        self.geometry_tree.column("valor", width=160, anchor="e")
        self.geometry_tree.pack(fill="both", expand=True)

        bom_columns = (
            "role", "code", "desc", "length", "qty_unit", "qty_order",
            "unit_price", "cost_unit", "cost_order"
        )
        bom_frame = ttk.Frame(bom_tab)
        bom_frame.pack(fill="both", expand=True)
        bom_frame.columnconfigure(0, weight=1)
        bom_frame.rowconfigure(0, weight=1)

        self.bom_tree = ttk.Treeview(
            bom_frame, columns=bom_columns, show="headings", height=18
        )
        headings = {
            "role": "Componente",
            "code": "Código",
            "desc": "Descrição",
            "length": "Comp. (mm)",
            "qty_unit": "Qtd./un.",
            "qty_order": "Qtd. pedido",
            "unit_price": "R$/m",
            "cost_unit": "Custo/un.",
            "cost_order": "Custo pedido",
        }
        widths = {
            "role": 145, "code": 85, "desc": 260, "length": 100,
            "qty_unit": 80, "qty_order": 95, "unit_price": 90,
            "cost_unit": 105, "cost_order": 110,
        }
        anchors = {
            "role": "w", "code": "center", "desc": "w", "length": "e",
            "qty_unit": "e", "qty_order": "e", "unit_price": "e",
            "cost_unit": "e", "cost_order": "e",
        }
        for c in bom_columns:
            self.bom_tree.heading(c, text=headings[c])
            self.bom_tree.column(c, width=widths[c], anchor=anchors[c], stretch=(c == "desc"))

        yscroll = ttk.Scrollbar(bom_frame, orient="vertical", command=self.bom_tree.yview)
        xscroll = ttk.Scrollbar(bom_frame, orient="horizontal", command=self.bom_tree.xview)
        self.bom_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.bom_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self.warning_text = tk.Text(
            warn_tab, wrap="word", height=18, font=("Segoe UI", 10), state="disabled"
        )
        self.warning_text.pack(fill="both", expand=True)

        footer = ttk.Frame(parent)
        footer.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        footer.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Preencha os dados e clique em CALCULAR.")
        ttk.Label(footer, textvariable=self.status_var, style="SmallMuted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.version_var = tk.StringVar(value="Engine: —")
        ttk.Label(footer, textvariable=self.version_var, style="SmallMuted.TLabel").grid(
            row=0, column=1, sticky="e"
        )

    def _summary_card(self, parent, col, title, variable):
        card = ttk.LabelFrame(parent, text=f" {title} ", style="Section.TLabelframe", padding=10)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 5, 0))
        label = ttk.Label(card, textvariable=variable, style="BigValue.TLabel", anchor="center")
        label.pack(fill="both", expand=True, pady=3)

    def _set_defaults(self):
        self.width_var.set("1500")
        self.height_var.set("1200")
        self.quantity_var.set("1")
        self.leaf_count_var.set("2")
        self.system_var.set("Janela PRIME 42x66")
        self.screen_var.set(False)
        self.shutter_var.set(False)

    def _build_config(self) -> SlidingConfiguration:
        width = parse_number(self.width_var.get(), "largura")
        height = parse_number(self.height_var.get(), "altura")
        qty = parse_number(self.quantity_var.get(), "quantidade", integer=True)
        leaves = parse_number(self.leaf_count_var.get(), "número de folhas", integer=True)
        system_label = self.system_var.get()
        if system_label not in SYSTEM_LABELS:
            raise ValueError("Selecione o sistema de folha.")
        return SlidingConfiguration(
            width_mm=width,
            height_mm=height,
            quantity=qty,
            leaf_count=leaves,
            leaf_system=SYSTEM_LABELS[system_label],
            screen_enabled=self.screen_var.get(),
            shutter_enabled=self.shutter_var.get(),
        )

    def calculate(self):
        try:
            cfg = self._build_config()
            result = calculate_sliding(cfg)
        except Exception as exc:
            messagebox.showerror("Não foi possível calcular", str(exc), parent=self)
            return

        self.current_cfg = cfg
        self.current_result = result
        self._render_result(cfg, result)

    def _render_result(self, cfg, result):
        self.model_value.set(result.model_description)
        self.unit_cost_value.set(money(result.unit_cost))
        self.order_cost_value.set(money(result.unit_cost * cfg.quantity))
        self.version_var.set(f"Engine: {result.calculation_version}")

        # Diferença Excel opcional
        excel_raw = self.excel_cost_var.get().strip()
        if excel_raw:
            try:
                excel_cost = parse_number(excel_raw, "custo esperado no Excel")
                diff = result.unit_cost - excel_cost
                pct = (diff / excel_cost * 100.0) if excel_cost else 0.0
                self.diff_value.set(f"{money(diff)} ({pct:+.2f}%)")
            except ValueError:
                self.diff_value.set("Valor Excel inválido")
        else:
            self.diff_value.set("—")

        # Geometria
        for item in self.geometry_tree.get_children():
            self.geometry_tree.delete(item)
        for key, value in result.geometry.items():
            self.geometry_tree.insert(
                "", "end",
                values=(GEOMETRY_LABELS.get(key, key), f"{value:,.3f} mm".replace(",", "X").replace(".", ",").replace("X", "."))
            )

        # BOM
        for item in self.bom_tree.get_children():
            self.bom_tree.delete(item)
        for comp in result.unit_bom:
            order_cost = comp.cost_per_unit_product * cfg.quantity
            self.bom_tree.insert(
                "", "end",
                values=(
                    ROLE_LABELS.get(comp.role, comp.role),
                    comp.material_code,
                    comp.description,
                    "" if comp.length_mm is None else f"{comp.length_mm:.3f}",
                    f"{comp.quantity_per_unit:g}",
                    f"{comp.quantity_order:g}",
                    money(comp.unit_price),
                    money(comp.cost_per_unit_product),
                    money(order_cost),
                ),
            )

        # Alertas
        self.warning_text.configure(state="normal")
        self.warning_text.delete("1.0", "end")
        if result.warnings:
            for warning in result.warnings:
                self.warning_text.insert("end", f"[{warning.code}]\n{warning.message}\n\n")
        else:
            self.warning_text.insert("end", "Nenhum alerta para esta configuração.")
        self.warning_text.configure(state="disabled")

        self.status_var.set(
            f"Cálculo concluído • {len(result.unit_bom)} componentes no BOM • "
            f"{len(result.warnings)} alerta(s)"
        )

    def clear_results(self):
        self.current_cfg = None
        self.current_result = None
        self.excel_cost_var.set("")
        self.notes_var.set("")
        self.model_value.set("—")
        self.unit_cost_value.set("—")
        self.order_cost_value.set("—")
        self.diff_value.set("—")
        self.version_var.set("Engine: —")
        self.status_var.set("Resultados limpos. Os dados de entrada foram mantidos.")

        for tree in (self.geometry_tree, self.bom_tree):
            for item in tree.get_children():
                tree.delete(item)

        self.warning_text.configure(state="normal")
        self.warning_text.delete("1.0", "end")
        self.warning_text.configure(state="disabled")

    def _cases_dir(self) -> Path:
        path = PROJECT_ROOT / "test_cases"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_test_case(self):
        if not self.current_cfg or not self.current_result:
            messagebox.showwarning(
                "Sem cálculo",
                "Faça um cálculo antes de salvar o caso de teste.",
                parent=self,
            )
            return

        excel_cost = None
        diff = None
        diff_pct = None
        raw = self.excel_cost_var.get().strip()
        if raw:
            try:
                excel_cost = parse_number(raw, "custo esperado no Excel")
                diff = self.current_result.unit_cost - excel_cost
                diff_pct = (diff / excel_cost * 100.0) if excel_cost else None
            except ValueError as exc:
                messagebox.showerror("Valor inválido", str(exc), parent=self)
                return

        now = datetime.now()
        cfg = self.current_cfg
        result = self.current_result

        bom = [asdict(x) for x in result.unit_bom]
        warnings = [asdict(x) for x in result.warnings]

        row = {
            "timestamp": now.isoformat(timespec="seconds"),
            "calculation_version": result.calculation_version,
            "width_mm": cfg.width_mm,
            "height_mm": cfg.height_mm,
            "quantity": cfg.quantity,
            "leaf_count": cfg.leaf_count,
            "leaf_system": cfg.leaf_system.value,
            "screen_enabled": cfg.screen_enabled,
            "shutter_enabled": cfg.shutter_enabled,
            "engine_unit_cost": result.unit_cost,
            "engine_order_cost": result.unit_cost * cfg.quantity,
            "excel_expected_unit_cost": "" if excel_cost is None else excel_cost,
            "difference_value": "" if diff is None else diff,
            "difference_pct": "" if diff_pct is None else diff_pct,
            "notes": self.notes_var.get().strip(),
            "geometry_json": json.dumps(result.geometry, ensure_ascii=False),
            "warnings_json": json.dumps(warnings, ensure_ascii=False),
            "bom_json": json.dumps(bom, ensure_ascii=False),
        }

        csv_path = self._cases_dir() / "golden_cases.csv"
        exists = csv_path.exists()
        with csv_path.open("a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()), delimiter=";")
            if not exists:
                writer.writeheader()
            writer.writerow(row)

        # Também salva um JSON individual, útil para testes automatizados futuros.
        case_id = f"CR_{now.strftime('%Y%m%d_%H%M%S')}_{cfg.leaf_count}F"
        json_path = self._cases_dir() / f"{case_id}.json"
        payload = {
            "case_id": case_id,
            "input": {
                "width_mm": cfg.width_mm,
                "height_mm": cfg.height_mm,
                "quantity": cfg.quantity,
                "leaf_count": cfg.leaf_count,
                "leaf_system": cfg.leaf_system.value,
                "screen_enabled": cfg.screen_enabled,
                "shutter_enabled": cfg.shutter_enabled,
            },
            "expected_excel": {
                "unit_cost": excel_cost,
            },
            "engine_result": {
                "calculation_version": result.calculation_version,
                "model_description": result.model_description,
                "geometry": result.geometry,
                "unit_cost": result.unit_cost,
                "order_cost": result.unit_cost * cfg.quantity,
                "bom": bom,
                "warnings": warnings,
            },
            "comparison": {
                "difference_value": diff,
                "difference_pct": diff_pct,
            },
            "notes": self.notes_var.get().strip(),
        }
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        messagebox.showinfo(
            "Caso salvo",
            f"Caso registrado com sucesso.\n\nCSV: {csv_path.name}\nJSON: {json_path.name}",
            parent=self,
        )
        self.status_var.set(f"Caso de teste salvo: {case_id}")

    def export_json(self):
        if not self.current_cfg or not self.current_result:
            messagebox.showwarning(
                "Sem cálculo",
                "Faça um cálculo antes de exportar.",
                parent=self,
            )
            return

        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar resultado",
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json")],
            initialfile="resultado_cr.json",
        )
        if not target:
            return

        payload = {
            "input": {
                **asdict(self.current_cfg),
                "leaf_system": self.current_cfg.leaf_system.value,
            },
            "result": {
                "calculation_version": self.current_result.calculation_version,
                "model_description": self.current_result.model_description,
                "geometry": self.current_result.geometry,
                "unit_cost": self.current_result.unit_cost,
                "cost_breakdown": self.current_result.cost_breakdown,
                "bom": [asdict(x) for x in self.current_result.unit_bom],
                "warnings": [asdict(x) for x in self.current_result.warnings],
            },
        }
        Path(target).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.status_var.set(f"Resultado exportado: {Path(target).name}")

    def open_cases_folder(self):
        folder = self._cases_dir()
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as exc:
            messagebox.showinfo(
                "Pasta dos casos",
                f"Os casos ficam em:\n{folder}\n\nNão foi possível abrir automaticamente: {exc}",
                parent=self,
            )


if __name__ == "__main__":
    app = EsquadriasTester()
    app.mainloop()
