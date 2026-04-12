"""
Ingestion adapters for retrieving raw data into canonical representations.
"""

from .base import IngestionAdapter, IngestionConfig
from .excel_adapter import CVMExcelAdapter
from .csv_adapter import CVMCSVAdapter
from .pdf_adapter import PDFAdapter

__all__ = [
    "IngestionAdapter",
    "IngestionConfig",
    "CVMExcelAdapter",
    "CVMCSVAdapter",
    "PDFAdapter",
]
