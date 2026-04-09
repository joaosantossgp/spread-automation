# processing/dre.py — Aplicação manual de DRE trimestral
# v2: label-based matching — escaneia col B do Spread para encontrar linhas pelos
# rótulos, sem depender de offsets fixos. Suporta múltiplas contas CVM somadas
# na mesma linha do Spread (ex: Perdas NRA + Outras Despesas Operacionais).

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from core.utils import normaliza_num, DRE_SPREAD_MAP


def aplicar_dre_manual(
    df_dre: pd.DataFrame, sheet,
    col_dst_1based: int, start_row: int,
    col_valor: str, is_xlwings: bool
) -> None:
    """
    Preenche as linhas da DRE no Spread usando mapeamento por rótulo (col B).

    Para cada entrada em DRE_SPREAD_MAP {cvm_desc: spread_label}:
      1. Procura a linha no Spread onde col B == spread_label
      2. Busca o valor na Origem CVM pela descrição da conta
      3. Acumula (soma) caso múltiplas contas CVM mapeiem para o mesmo rótulo
      4. Grava o total acumulado na célula encontrada

    Args:
        df_dre:        DataFrame da DRE da Origem (com col "Descricao Conta")
        sheet:         Worksheet do Spread (openpyxl ou xlwings)
        col_dst_1based: Índice 1-based da coluna destino no Spread
        start_row:     Primeira linha a escanear na col B (normalmente start_row=27)
        col_valor:     Nome da coluna no df_dre com os valores (ex: "3T25")
        is_xlwings:    True se sheet for xlwings, False se for openpyxl
    """
    # 1. Constrói mapa label → número de linha escaneando col B
    label_to_row: dict[str, int] = {}
    if is_xlwings:
        r = start_row
        while r <= 400:
            label = sheet.cells(r, 2).value
            if label not in (None, ""):
                label_to_row[str(label).strip()] = r
            r += 1
    else:
        for row_cells in sheet.iter_rows(min_row=start_row, max_col=2):
            cell = row_cells[1]  # col B (índice 1 em iter_rows)
            if cell.value not in (None, ""):
                label_to_row[str(cell.value).strip()] = cell.row

    # 2. Acumula valores por rótulo do Spread
    sums: dict[str, int | None] = defaultdict(lambda: None)
    for cvm_desc, spread_label in DRE_SPREAD_MAP.items():
        if spread_label not in label_to_row:
            continue
        try:
            raw = df_dre.loc[
                df_dre["Descricao Conta"].str.strip() == cvm_desc,
                col_valor
            ].iloc[0]
        except (IndexError, KeyError):
            continue
        val = normaliza_num(raw)
        if val is None:
            continue
        prev = sums[spread_label]
        sums[spread_label] = val if prev is None else prev + val

    # 3. Grava os totais acumulados
    for label, total in sums.items():
        if total is None:
            continue
        r = label_to_row[label]
        if is_xlwings:
            sheet.cells(r, col_dst_1based).value = total
        else:
            sheet.cell(r, col_dst_1based, value=total)
