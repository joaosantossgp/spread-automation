from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.models import FinancialDataSet, EntityType


@dataclass(frozen=True, slots=True)
class IngestionConfig:
    """Configuration for data ingestion."""
    path: str | Path
    company: str
    period: str
    entity_type: EntityType = EntityType.CONSOLIDATED
    cnpj: str | None = None
    section: str | None = None
    previous_period: str | None = None
    previous_previous_period: str | None = None


class IngestionAdapter(ABC):
    """
    Base class for all ingestion adapters.
    Adapters are responsible for taking a raw source document (Excel, CSV, PDF, etc.)
    and transforming it into a canonical FinancialDataSet.
    """

    @abstractmethod
    def load(self, config: IngestionConfig) -> FinancialDataSet:
        """
        Parses the source data and returns a standardized FinancialDataSet.
        """
        pass
