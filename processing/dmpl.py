# processing/dmpl.py — Inserção de Dividendos, JCP e Aumentos de Capital (DMPL)
# Extraído de app_spread.py
#
# v2 — Camada 1 aplicada à DMPL:
#   Lookup primário por CD_CONTA exato (5.04.06, 5.04.07, 5.04.01) definido em
#   core/conta_map.py. Fallback por busca textual na DescricaoConta (comportamento
#   original) caso os códigos não sejam encontrados.
#
# ESTRUTURA DMPL no Plano de Contas Fixas CVM (DF Cons. - DMPL):
#   5.04.01  Aumentos de Capital
#   5.04.06  Dividendos
#   5.04.07  Juros sobre Capital Próprio
#   A coluna de valor usada é "Patrimônio líquido Consolidado" (cons) ou
#   "Patrimônio Líquido" (ind). O código usa regex para encontrá-la.

from __future__ import annotations

import re

import pandas as pd

from core.utils import normaliza_num
from core.conta_map import DMPL_DIVIDENDOS_CODES, DMPL_JCP_CODES, DMPL_CAPITAL_CODES


def _col_valor_dmpl(df_dm: pd.DataFrame) -> str | None:
    """Encontra a coluna de PL total no DataFrame da DMPL."""
    for col in df_dm.columns:
        if re.search(r'patrim[oô]nio.*consolidado', col, flags=re.I):
            return col
    for col in df_dm.columns:
        if re.search(r'patrim[oô]nio.*l[íi]quido', col, flags=re.I):
            return col
    return None


def _col_codigo_dmpl(df_dm: pd.DataFrame) -> str | None:
    """Encontra a coluna de código de conta no DataFrame da DMPL."""
    for col in df_dm.columns:
        if re.search(r'c[oó]digo.*conta|codigoconta', col, flags=re.I):
            return col
    return None


def _col_desc_dmpl(df_dm: pd.DataFrame) -> str | None:
    """Encontra a coluna de descrição de conta no DataFrame da DMPL."""
    for col in df_dm.columns:
        if re.search(r'desc.*conta|descricaoconta', col, flags=re.I):
            return col
    return None


def _buscar_por_codigo(
    df_dm: pd.DataFrame, col_codigo: str, col_valor: str, codes: list[str]
) -> list[int]:
    """Camada 1: busca valores por CD_CONTA exato. Retorna lista de inteiros não-nulos."""
    mask = df_dm[col_codigo].astype(str).isin(codes)
    return [n for v in df_dm.loc[mask, col_valor]
            if (n := normaliza_num(v)) is not None]


def _buscar_por_texto(
    df_dm: pd.DataFrame, col_desc: str, col_valor: str, pattern: str
) -> list[int]:
    """Camada 2 (fallback): busca valores por texto na DescricaoConta."""
    mask = df_dm[col_desc].astype(str).str.contains(pattern, case=False, na=False)
    return [n for v in df_dm.loc[mask, col_valor]
            if (n := normaliza_num(v)) is not None]


def _montar_e_gravar(
    nums: list[int], sheet, col: int, linha: int, is_xlwings: bool, positivo: bool
) -> int | None:
    """Monta valor ou fórmula e grava na célula. Retorna total."""
    if not nums:
        return None
    if positivo:
        total = sum(abs(n) for n in nums)
        val = total if len(nums) == 1 else f"={'+'.join(str(abs(n)) for n in nums)}"
    else:
        total = -sum(abs(n) for n in nums)
        terms = "".join(f"-{abs(n)}" for n in nums)
        val = total if len(nums) == 1 else f"={terms.lstrip('+')}"
    if is_xlwings:
        sheet.cells(linha, col).value = val
    else:
        sheet.cell(row=linha, column=col, value=val)
    return total


def inserir_dividendos_dm(
    df_dm: pd.DataFrame,
    sheet,
    col_dst_1based: int,
    linha_neg: int,
    linha_pos: int,
    is_xlwings: bool
) -> tuple[int | None, int | None]:
    """
    Insere na planilha:
      • em `linha_neg` : soma NEGATIVA de dividendos + JCP (valores que saem do PL)
      • em `linha_pos` : soma POSITIVA dessas mesmas contas (se existirem)

    Camada 1: busca por CD_CONTA 5.04.06 (Dividendos) e 5.04.07 (JCP).
    Camada 2 (fallback): busca por texto 'dividendo|juros sobre capital próprio'.
    """
    if df_dm is None:
        return None, None

    col_valor = _col_valor_dmpl(df_dm)
    if col_valor is None:
        return None, None

    # Camada 1: lookup por código
    col_codigo = _col_codigo_dmpl(df_dm)
    nums: list[int] = []
    if col_codigo:
        nums = _buscar_por_codigo(df_dm, col_codigo, col_valor,
                                  DMPL_DIVIDENDOS_CODES + DMPL_JCP_CODES)

    # Camada 2: fallback textual
    if not nums:
        col_desc = _col_desc_dmpl(df_dm)
        if col_desc:
            nums = _buscar_por_texto(df_dm, col_desc, col_valor,
                                     r"dividendo|juros sobre capital pr[oó]prio")

    if not nums:
        return None, None

    negs = [n for n in nums if n < 0]
    poss = [n for n in nums if n > 0]

    total_neg = _montar_e_gravar(negs, sheet, col_dst_1based, linha_neg, is_xlwings, positivo=False)
    total_pos = _montar_e_gravar(poss, sheet, col_dst_1based, linha_pos, is_xlwings, positivo=True)

    return total_neg, total_pos


def inserir_aumentos_capital_dm(
    df_dm: pd.DataFrame,
    sheet,
    col_dst_1based: int,
    linha: int,
    is_xlwings: bool
) -> int | None:
    """
    Insere soma de Aumentos de Capital (5.04.01) na linha do Spread.

    Camada 1: busca por CD_CONTA 5.04.01.
    Camada 2 (fallback): busca por texto 'aumento(s) de capital'.
    """
    if df_dm is None:
        return None

    col_valor = _col_valor_dmpl(df_dm)
    if col_valor is None:
        return None

    # Camada 1: lookup por código
    col_codigo = _col_codigo_dmpl(df_dm)
    nums: list[int] = []
    if col_codigo:
        nums = _buscar_por_codigo(df_dm, col_codigo, col_valor, DMPL_CAPITAL_CODES)

    # Camada 2: fallback textual
    if not nums:
        col_desc = _col_desc_dmpl(df_dm)
        if col_desc:
            nums = _buscar_por_texto(df_dm, col_desc, col_valor,
                                     r'aumentos?\s+de\s+capital')

    return _montar_e_gravar(nums, sheet, col_dst_1based, linha, is_xlwings, positivo=True)
