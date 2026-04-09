# app/gui.py — Interface gráfica (CustomTkinter) para o Atualizador de Spread
# v2: auto-detecção de colunas, checkbox multi-período, relatório melhor

from __future__ import annotations

import logging
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog

from processing.pipeline import processar, processar_multi, detectar_colunas


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Atualizador de Spread")
        self.grid_columnconfigure((0, 1), weight=1)

        # Arquivo Origem
        self.var_ori = ctk.StringVar()
        self._campo_arquivo("Arquivo Origem (DadosDocumento.xlsx)", 0, self.var_ori)

        # Arquivo Spread
        self.var_spr = ctk.StringVar()
        self._campo_arquivo("Arquivo Spread (Spread Proxy.xlsx)", 1, self.var_spr)

        # Tipo
        self.var_tipo = ctk.StringVar(value="consolidado")
        ctk.CTkLabel(self, text="Tipo").grid(row=2, column=0, sticky="w", padx=4)
        ctk.CTkOptionMenu(
            self, variable=self.var_tipo,
            values=["consolidado", "individual"]
        ).grid(row=2, column=1, sticky="ew", padx=4)

        # Período
        self.var_per = ctk.StringVar()
        self._campo_txt("Período (Ex: 2024 ou 4T24)", 3, self.var_per)

        # Colunas
        self.var_src = ctk.StringVar(value="auto")
        self._campo_txt("Coluna Origem (ou 'auto')", 4, self.var_src, width=80)
        self.var_dst = ctk.StringVar(value="auto")
        self._campo_txt("Coluna Destino (ou 'auto')", 5, self.var_dst, width=80)

        # Multi-período
        self.var_multi = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Preencher 2 períodos de uma vez (ant → atual)",
            variable=self.var_multi
        ).grid(row=6, column=0, columnspan=2, sticky="w", padx=4, pady=(5, 0))

        # Botões
        ctk.CTkButton(self, text="Processar", command=self._run).grid(
            row=10, column=0, pady=10, padx=4, sticky="ew"
        )
        ctk.CTkButton(self, text="Sair", fg_color="gray", command=self.destroy).grid(
            row=10, column=1, pady=10, padx=4, sticky="ew"
        )

        # Log
        self.log_box = ctk.CTkTextbox(self, width=600, height=200, state="disabled")
        self.log_box.grid(row=11, column=0, columnspan=2, pady=(5, 10), padx=4)
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    def _campo_arquivo(self, rotulo, linha, var):
        ctk.CTkLabel(self, text=rotulo).grid(row=linha, column=0, sticky="w", padx=4)
        ctk.CTkEntry(self, textvariable=var, width=420).grid(row=linha, column=1, sticky="ew", padx=4)

        def escolhe():
            f = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xlsm *.xls")])
            if f:
                var.set(f)

        ctk.CTkButton(self, text="…", width=30, command=escolhe).grid(row=linha, column=2, padx=2)

    def _campo_txt(self, rotulo, linha, var, width=420):
        ctk.CTkLabel(self, text=rotulo).grid(row=linha, column=0, sticky="w", padx=4)
        ctk.CTkEntry(self, textvariable=var, width=width).grid(row=linha, column=1, sticky="w", padx=4)

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _run(self):
        try:
            ori = Path(self.var_ori.get())
            spr = Path(self.var_spr.get())

            if not ori.exists():
                self._log("❌ Arquivo Origem não encontrado.")
                return
            if not spr.exists():
                self._log("❌ Arquivo Spread não encontrado.")
                return

            periodo = self.var_per.get().strip()
            if not periodo:
                self._log("❌ Informe o período (ex: 2024 ou 4T24).")
                return

            # Auto-detecção de colunas
            src_txt = self.var_src.get().strip()
            dst_txt = self.var_dst.get().strip()
            is_trimestral = any(c.isalpha() for c in periodo) and "T" in periodo.upper()

            if src_txt.lower() == "auto" or dst_txt.lower() == "auto":
                self._log("🔍 Detectando colunas automaticamente...")
                try:
                    detected_src, detected_dst = detectar_colunas(
                        spr, trimestral=is_trimestral
                    )
                    if src_txt.lower() == "auto":
                        src_txt = detected_src
                    if dst_txt.lower() == "auto":
                        dst_txt = detected_dst
                    self._log(f"   Detectado: Origem={src_txt}, Destino={dst_txt}")
                except Exception as e:
                    self._log(f"❌ Falha na auto-detecção: {e}")
                    return

            # Multi-período ou período único
            if self.var_multi.get():
                self._log("═══ Modo multi-período ═══")
                out = processar_multi(
                    ori=ori, spr=spr, tipo=self.var_tipo.get(),
                    periodo=periodo, src_txt=src_txt,
                    start_row=27,
                    out_dir=None, log=self._log
                )
            else:
                out = processar(
                    ori=ori, spr=spr, tipo=self.var_tipo.get(),
                    periodo=periodo,
                    src_txt=src_txt, dst_txt=dst_txt,
                    start_row=27,
                    out_dir=None, log=self._log
                )

            self._log(f"\n✔️ Finalizado: {out}")
        except Exception as e:
            logging.exception("Erro no processamento")
            self._log(f"\n❌ Erro: {e}")
