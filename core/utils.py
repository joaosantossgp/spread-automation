# core/utils.py — funções utilitárias puras e constantes
# Extraído de app_spread.py (v8)

from __future__ import annotations

import re
from typing import Callable, Set, Tuple

import pandas as pd
from openpyxl.utils import (
    column_index_from_string as col2idx,
    get_column_letter as idx2col,
)

try:
    import xlwings as xw
    XLWINGS = True
except ImportError:
    XLWINGS = False


def normaliza_num(v) -> int | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        s = v.strip().replace(".", "").replace(",", "")
        if re.fullmatch(r"-?\d+", s):
            return int(s)
    return None


def periodos(p: str) -> Tuple[str, str, str, bool]:
    p = p.upper().strip()
    if re.fullmatch(r"\d{4}", p):
        a = int(p)
        return str(a), str(a-1), str(a-2), False
    m = re.fullmatch(r"([1-4])T(\d{2})", p)
    if not m:
        raise ValueError("Período deve ser AAAA ou nTAA (ex.: 2024 ou 1T25).")
    tri, aa = int(m.group(1)), int(m.group(2))
    f = lambda y: f"{tri}T{y:02d}"
    return f(aa), f(aa-1), f(aa-2), True


def col_txt_to_idx(txt: str) -> int:
    t = txt.strip().upper()
    if t.isdigit():
        return int(t)
    return col2idx(t) - 1


def shift_formula(f: str, delta: int) -> str:
    pat = re.compile(
        r"(?<![A-Za-z0-9_])(?:'[^']+'|[A-Za-z0-9_]+)?!"
        r"|(?<![A-Za-z0-9_])(\$?)([A-Za-z]{1,3})(?=\$?\d|:)",
        flags=re.I,
    )
    def repl(m):
        if m.group(1) is None:
            return m.group(0)
        abs_, col = m.group(1), m.group(2)
        try:
            return f"{abs_}{idx2col(col2idx(col)+delta)}"
        except:
            return col
    return pat.sub(repl, f)


def adjust_complex_formula(
    formula: str, delta: int,
    map_number: Callable[[int], int|None],
    used_vals: Set[int]|None=None
) -> str:
    num_pat = re.compile(r"(?<![A-Za-z])[-+]?\d[\d\.,]*")
    f2 = shift_formula(formula, delta)
    def repl(m):
        n = normaliza_num(m.group(0))
        novo = map_number(n)
        if novo is not None and used_vals is not None:
            used_vals.add(novo)
            return str(novo)
        return m.group(0)
    return num_pat.sub(repl, f2)


# ---------------------------------------------------------------------------
# Mapeamento DRE trimestral: conta CVM → rótulo na col B do Spread
# ---------------------------------------------------------------------------
# Múltiplas contas CVM podem apontar para o mesmo rótulo — os valores são SOMADOS.
# A função aplicar_dre_manual (processing/dre.py) escaneia a col B do Spread
# para encontrar as linhas pelos rótulos, sem depender de offsets fixos.
DRE_SPREAD_MAP: dict[str, str] = {
    # Convenção: Receita total CVM vai em "Vendas Mercado Externo" (independe do rótulo)
    "Receita de Venda de Bens e/ou Serviços":               "Vendas Mercado Externo",
    "Custo dos Bens e/ou Serviços Vendidos":                 "CMV Total",
    "Resultado Bruto":                                        "Lucro Bruto",
    "Despesas Gerais e Administrativas":                      "Despesas Administrativas",
    "Despesas com Vendas":                                    "Despesas de Vendas",
    "Outras Despesas Operacionais":                           "Outras Despesas Operacionais",
    "Perdas pela Não Recuperabilidade de Ativos":             "Outras Despesas Operacionais",
    "Outras Receitas Operacionais":                           "Outras Receitas Operacionais",
    "Despesas Financeiras":                                   "Despesas Financeiras Caixa",
    "Receitas Financeiras":                                   "Receitas Financeiras Caixa",
    "Resultado de Equivalência Patrimonial":                  "Equivalência Patrimonial",
    "Imposto de Renda e Contribuição Social sobre o Lucro":   "Imposto de Renda",
    # Lucro Líquido NÃO é mapeado — calculado por fórmula no Spread
}
