# processing/dfc.py — Inserção de Depreciação/Amortização (DFC)
# Extraído de app_spread.py

from __future__ import annotations

import pandas as pd

from core.utils import normaliza_num


def inserir_depreciacao_dfc(
    df_dfc: pd.DataFrame, sheet,
    col_dst_1based: int, linha: int,
    col_valor: str, is_xlwings: bool
) -> int | None:
    if df_dfc is None or col_valor not in df_dfc.columns:
        return None
    # Filtra apenas atividades operacionais (6.01.x) para evitar capturar
    # amortizações de empréstimos/financiamentos que ficam em 6.03.
    # Ex: Sabesp tem 6.03.02 "Amortizações" (pagamento de dívida) que o regex
    # genérico capturaria erroneamente.
    if "Codigo Conta" in df_dfc.columns:
        oper = df_dfc["Codigo Conta"].astype(str).str.startswith("6.01")
        df_oper = df_dfc[oper]
    else:
        df_oper = df_dfc
    desc = df_oper["Descricao Conta"].astype(str)
    # exaustão adicionada para empresas de mineração/petróleo
    mask = desc.str.contains(r"deprecia|amortiza|exaustão|exaustao", case=False, na=False)
    nums = [normaliza_num(v) for v in df_oper.loc[mask, col_valor]]
    nums = [n for n in nums if n is not None]
    if not nums:
        return None
    if len(nums) == 1:
        total = -abs(nums[0])
        val = total
    else:
        terms = "".join(f"-{abs(n)}" for n in nums)
        total = -sum(abs(n) for n in nums)
        val = f"={terms.lstrip('+')}"
    if is_xlwings:
        sheet.cells(linha, col_dst_1based).value = val
    else:
        sheet.cell(linha, col_dst_1based, value=val)
    return total
