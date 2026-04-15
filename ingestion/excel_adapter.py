from pathlib import Path
from decimal import Decimal, InvalidOperation
import pandas as pd

from .base import IngestionAdapter, IngestionConfig
from core.models import FinancialDataSet, FinancialAccount, EntityType, SourceType


class CVMExcelAdapter(IngestionAdapter):
    """
    Adapter to parse CVM 'DadosDocumento.xlsx' individual or consolidated
    files into a canonical FinancialDataSet.
    """

    def load(self, config: IngestionConfig) -> FinancialDataSet:

        if not config.entity_type or config.entity_type not in list(EntityType):
            raise ValueError(
                f"Invalid or missing entity_type '{config.entity_type}' received during Excel data ingestion. "
                f"Expected one of {[e.value for e in EntityType]}."
            )

        path = Path(config.path)
        is_trim = "T" in config.period.upper()
        
        chapa = "Cons" if config.entity_type == EntityType.CONSOLIDATED else "Ind"
        aba_dm_atual = f"DF {chapa} DMPL Atual"
        aba_dm_ultimo = f"DF {chapa} DMPL Ultimo"
        
        sheet_map = {
            f"DF {chapa} Ativo": "ATIVO",
            f"DF {chapa} Passivo": "PASSIVO",
            f"DF {chapa} Resultado Periodo": "DRE",
            f"DF {chapa} Fluxo de Caixa": "DFC",
            aba_dm_atual: "DMPL",
            aba_dm_ultimo: "DMPL",
        }

        engine = "openpyxl" if path.suffix.lower() in (".xlsx", ".xlsm") else None
        xls = pd.ExcelFile(path, engine=engine)
        
        accounts = []
        
        for sheet_orig, section in sheet_map.items():
            if sheet_orig not in xls.sheet_names:
                continue
                
            df = pd.read_excel(xls, sheet_name=sheet_orig, engine=engine)
            
            col_map = {col: i for i, col in enumerate(df.columns)}

            def get_val(r, *col_names, default=None):
                for col_name in col_names:
                    idx = col_map.get(col_name)
                    if idx is not None:
                        return r[idx]
                return default

            for row in df.itertuples(index=False, name=None):
                # Extract code and description
                codigo = str(get_val(row, "Codigo Conta", "CodigoConta", default="")).strip()
                descricao = str(get_val(row, "Descricao Conta", "DescricaoConta", default="")).strip()
                
                if not codigo or not descricao:
                    continue
                    
                # Identify value columns
                if section == "DMPL":
                    # For DMPL, we look for 'Patrimonio liquido Consolidado' or 'Patrimonio Liquido'
                    val_col = "Patrimônio líquido Consolidado" if config.entity_type == EntityType.CONSOLIDATED else "Patrimônio Líquido"
                    if val_col not in df.columns:
                        val_col = "Patrimonio liquido Consolidado" if config.entity_type == EntityType.CONSOLIDATED else "Patrimonio Liquido"
                    if val_col in df.columns:
                        val = get_val(row, val_col)
                        if pd.notna(val):
                            accounts.append(FinancialAccount(
                                code=codigo,
                                description=descricao,
                                value=_coerce_decimal(val),
                                period=config.period,
                                section=section,
                                source=SourceType.CVM_EXCEL
                            ))
                else:
                    # Period matching logic based on core/origin
                    val_atual = None
                    val_ant = None
                    val_ant2 = None
                    
                    if is_trim:
                        if section in ("ATIVO", "PASSIVO"):
                            val_atual = get_val(row, "Valor Trimestre Atual", "Valor Ultimo Exercicio")
                            val_ant = get_val(row, "Valor Exercicio Anterior", "Valor Penultimo Exercicio")
                        else:
                            val_atual = get_val(row, "Valor Acumulado Atual Exercicio", "Valor Ultimo Exercicio")
                            val_ant = get_val(row, "Valor Acumulado Exercicio Anterior", "Valor Penultimo Exercicio")
                    else:
                        val_atual = get_val(row, "Valor Ultimo Exercicio")
                        val_ant = get_val(row, "Valor Penultimo Exercicio")
                        val_ant2 = get_val(row, "Valor Antepenultimo Exercicio")
                    
                    # Add current period account
                    if val_atual is not None and pd.notna(val_atual):
                        accounts.append(FinancialAccount(
                            code=codigo,
                            description=descricao,
                            value=_coerce_decimal(val_atual),
                            period=config.period,
                            section=section,
                            source=SourceType.CVM_EXCEL
                        ))
                    
                    # Add previous period account
                    if val_ant is not None and pd.notna(val_ant) and config.previous_period:
                        accounts.append(FinancialAccount(
                            code=codigo,
                            description=descricao,
                            value=_coerce_decimal(val_ant),
                            period=config.previous_period,
                            section=section,
                            source=SourceType.CVM_EXCEL
                        ))
                        
                    # Add previous-previous period account if DFP
                    if not is_trim and val_ant2 is not None and pd.notna(val_ant2) and config.previous_previous_period:
                        accounts.append(FinancialAccount(
                            code=codigo,
                            description=descricao,
                            value=_coerce_decimal(val_ant2),
                            period=config.previous_previous_period,
                            section=section,
                            source=SourceType.CVM_EXCEL
                        ))

        return FinancialDataSet(
            company=config.company,
            cnpj=config.cnpj,
            period=config.period,
            entity_type=config.entity_type,
            source_type=SourceType.CVM_EXCEL,
            accounts=accounts
        )


def _coerce_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise InvalidOperation("Empty numeric string.")

        normalized = text.replace(" ", "")
        if "." in normalized and "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            comma_parts = normalized.split(",")
            if len(comma_parts) == 2 and comma_parts[1].isdigit() and len(comma_parts[1]) <= 2:
                normalized = normalized.replace(",", ".")
            else:
                normalized = normalized.replace(",", "")
        else:
            dot_parts = normalized.split(".")
            if len(dot_parts) > 2:
                normalized = normalized.replace(".", "")
            elif len(dot_parts) == 2 and dot_parts[1].isdigit() and len(dot_parts[1]) == 3:
                normalized = normalized.replace(".", "")

        return Decimal(normalized)

    return Decimal(str(value))
