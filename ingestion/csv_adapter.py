import pandas as pd
from pathlib import Path
from decimal import Decimal

from .base import IngestionAdapter, IngestionConfig
from core.models import FinancialDataSet, FinancialAccount, EntityType, SourceType


class CVMCSVAdapter(IngestionAdapter):
    """
    Adapter to parse Data provided by CVM in open data standard (CSV format).
    """

    def load(self, config: IngestionConfig) -> FinancialDataSet:
        path = Path(config.path)
        
        df = pd.read_csv(path, sep=";", encoding="utf-8")
        
        # Apply filters
        if config.cnpj:
            df = df[df["CNPJ_CIA"] == config.cnpj]
        else:
            df = df[df["DENOM_CIA"].str.contains(config.company, case=False, na=False)]
            
        accounts = []
        for _, row in df.iterrows():
            codigo = str(row.get("CD_CONTA", "")).strip()
            descricao = str(row.get("DS_CONTA", "")).strip()
            valor = row.get("VL_CONTA")
            
            if not codigo or not descricao or pd.isna(valor):
                continue
                
            accounts.append(
                FinancialAccount(
                    code=codigo,
                    description=descricao,
                    value=Decimal(str(valor)),
                    period=config.period,  # Needs proper mapping dynamically based on CSV DT_REFER/ORDEM
                    section=config.section or "UNKNOWN",
                    source=SourceType.CVM_CSV
                )
            )

        return FinancialDataSet(
            company=config.company,
            cnpj=config.cnpj,
            period=config.period,
            entity_type=config.entity_type,
            source_type=SourceType.CVM_CSV,
            accounts=accounts
        )
