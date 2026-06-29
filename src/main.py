from __future__ import annotations

import csv
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    APP_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = APP_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bddk_loader import load_bddk_accounts  # noqa: E402
from comparator import CompareResult, CoaComparator  # noqa: E402
from config_loader import load_config, project_root  # noqa: E402
from sql_loader import load_coa_from_sql  # noqa: E402


STATUS_FILTERS = [
    "TUMU",
    "TAM_ESLESME",
    "KISMEN_ESLESME",
    "KOD_ESLESTI_ISIM_FARKLI",
    "SADECE_BDDK",
    "SADECE_COA",
]


class CompareApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("COA - BDDK Karsilastirma")
        self.geometry("1400x720")
        self.minsize(1080, 560)

        self.config_path = project_root() / "config.json"
        self.results: list[CompareResult] = []
        self.last_query = ""

        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Karsilastir", command=self.run_compare).pack(side="left")
        ttk.Button(toolbar, text="Excel Disa Aktar", command=self.export_csv).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Config Ac", command=self.open_config).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Sorgu Dosyasi Ac", command=self.open_query_file).pack(side="left", padx=(8, 0))

        self.status_filter = tk.StringVar(value="TUMU")
        ttk.Label(toolbar, text="Filtre").pack(side="left", padx=(16, 4))
        ttk.Combobox(
            toolbar,
            textvariable=self.status_filter,
            values=STATUS_FILTERS,
            state="readonly",
            width=24,
        ).pack(side="left")
        ttk.Button(toolbar, text="Uygula", command=self.apply_filter).pack(side="left", padx=(8, 0))

        info = ttk.Frame(self, padding=(8, 0))
        info.pack(fill="x")
        self.info_var = tk.StringVar(value="Hazir.")
        ttk.Label(info, textvariable=self.info_var).pack(anchor="w")

        columns = (
            "code",
            "bddk_code",
            "sql_code",
            "bddk_name",
            "sql_name",
            "status",
            "similarity",
            "detail",
        )
        table_frame = ttk.Frame(self, padding=8)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "code": "Kod",
            "bddk_code": "BDDK Kodu",
            "sql_code": "Sorgu Kodu",
            "bddk_name": "BDDK Adi",
            "sql_name": "Sorgu Hesap Adi",
            "status": "Durum",
            "similarity": "Benzerlik",
            "detail": "Aciklama",
        }
        widths = {
            "code": 90,
            "bddk_code": 90,
            "sql_code": 90,
            "bddk_name": 220,
            "sql_name": 220,
            "status": 170,
            "similarity": 90,
            "detail": 320,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def run_compare(self) -> None:
        try:
            config = load_config(self.config_path)
            self.info_var.set("SQL sorgusu calistiriliyor...")
            self.update_idletasks()

            records, query = load_coa_from_sql(config)
            self.last_query = query

            self.info_var.set("BDDK hesap plani yukleniyor...")
            self.update_idletasks()

            bddk_accounts = load_bddk_accounts(config.bddk_cache_file, config.bddk_url)
            comparator = CoaComparator(bddk_accounts)

            self.info_var.set("Kodlar birlestiriliyor ve karsilastiriliyor...")
            self.update_idletasks()

            self.results = comparator.compare_all(records)
            self.populate_tree(self.results)

            summary = self._summary(self.results)
            self.info_var.set(
                f"{len(self.results)} kod | Sorgu: {config.query_file.name} | {summary}"
            )
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))
            self.info_var.set("Islem basarisiz.")

    def populate_tree(self, rows: list[CompareResult]) -> None:
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.code,
                    row.bddk_code,
                    row.sql_code,
                    row.bddk_name,
                    row.sql_name,
                    row.status,
                    f"{row.similarity:.0%}" if row.similarity else "",
                    row.detail,
                ),
            )

    def apply_filter(self) -> None:
        selected = self.status_filter.get()
        if selected == "TUMU":
            self.populate_tree(self.results)
            return
        filtered = [row for row in self.results if row.status == selected]
        self.populate_tree(filtered)

    def export_csv(self) -> None:
        if not self.results:
            messagebox.showinfo("Bilgi", "Once karsilastirma calistirin.")
            return

        target = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="coa_bddk_karsilastirma.csv",
        )
        if not target:
            return

        with open(target, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(
                [
                    "Kod",
                    "BddkKodu",
                    "SorguKodu",
                    "BddkAdi",
                    "SorguHesapAdi",
                    "Durum",
                    "Benzerlik",
                    "Aciklama",
                ]
            )
            for row in self.results:
                writer.writerow(
                    [
                        row.code,
                        row.bddk_code,
                        row.sql_code,
                        row.bddk_name,
                        row.sql_name,
                        row.status,
                        f"{row.similarity:.4f}" if row.similarity else "",
                        row.detail,
                    ]
                )

        messagebox.showinfo("Tamam", f"Dosya kaydedildi:\n{target}")

    def open_config(self) -> None:
        path = self.config_path
        if not path.exists():
            messagebox.showerror("Hata", f"Config bulunamadi: {path}")
            return
        import os

        os.startfile(path)

    def open_query_file(self) -> None:
        config = load_config(self.config_path)
        path = config.query_file
        if not path.exists():
            messagebox.showerror("Hata", f"Sorgu dosyasi bulunamadi: {path}")
            return
        import os

        os.startfile(path)

    @staticmethod
    def _summary(rows: list[CompareResult]) -> str:
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.status] = counts.get(row.status, 0) + 1
        parts = [f"{key}: {value}" for key, value in sorted(counts.items())]
        return " | ".join(parts)


def main() -> None:
    app = CompareApp()
    app.mainloop()


if __name__ == "__main__":
    main()
