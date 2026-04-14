# processing/dre.py — Aplicação manual de DRE trimestral
# v2: label-based matching — escaneia col B do Spread para encontrar linhas pelos
# rótulos, sem depender de offsets fixos. Suporta múltiplas contas CVM somadas
# na mesma linha do Spread (ex: Perdas NRA + Outras Despesas Operacionais).

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from core.exceptions import SchemaError
from core.utils import normaliza_num
from processing.runtime_bridge import mapping_registry, spread_schema


def aplicar_dre_manual(
    df_dre: pd.DataFrame, sheet,
    col_dst_1based: int, start_row: int,
    col_valor: str, is_xlwings: bool
) -> None:
    """
    Preenche as linhas da DRE no Spread usando o MappingRegistry Layer 2.

      1. Resolve a descrição CVM para um row key canônico
      2. Acumula múltiplas contas CVM no mesmo row key
      3. Resolve a linha final pelo SpreadSchema
      4. Grava o total acumulado na célula encontrada

    Args:
        df_dre:        DataFrame da DRE da Origem (com col "Descricao Conta")
        sheet:         Worksheet do Spread (openpyxl ou xlwings)
        col_dst_1based: Índice 1-based da coluna destino no Spread
        start_row:     Mantido por compatibilidade com os callers legados
        col_valor:     Nome da coluna no df_dre com os valores (ex: "3T25")
        is_xlwings:    True se sheet for xlwings, False se for openpyxl
    """
    del start_row
    registry = mapping_registry()
    schema = spread_schema()

    sums: dict[str, int | None] = defaultdict(lambda: None)

    if "Descricao Conta" in df_dre.columns and col_valor in df_dre.columns:
        # Optimization: Drop missing values and vectorize resolution
        df_valid = df_dre.dropna(subset=["Descricao Conta", col_valor]).copy()
        if not df_valid.empty:
            df_valid['row_key'] = df_valid["Descricao Conta"].astype(str).apply(registry.layer2)
            df_valid = df_valid.dropna(subset=['row_key'])
            if not df_valid.empty:
                df_valid['norm_val'] = df_valid[col_valor].apply(normaliza_num)
                df_valid = df_valid.dropna(subset=['norm_val'])
                if not df_valid.empty:
                    # Group by row_key and sum the normalized values
                    grouped = df_valid.groupby('row_key')['norm_val'].sum()
                    for k, v in grouped.items():
                        prev = sums[k]
                        sums[k] = int(v) if prev is None else prev + int(v)

    for row_key, total in sums.items():
        if total is None:
            continue
        try:
            row_number = schema.row_for(row_key)
        except SchemaError:
            continue
        if is_xlwings:
            sheet.cells(row_number, col_dst_1based).value = total
        else:
            sheet.cell(row_number, col_dst_1based, value=total)
