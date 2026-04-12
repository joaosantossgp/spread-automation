"""PDF adapter for ingestion."""

from pathlib import Path

from core.models import EntityType, SourceType, FinancialDataSet
from ingestion.base import IngestionAdapter, IngestionConfig
from .pdf.extractor import MarkdownExtractor
from .pdf.parser import MarkdownParser


class PDFAdapter(IngestionAdapter):
    """
    Adapter to parse PDF Document representations into FinancialDataSet.
    """

    def load(self, config: IngestionConfig) -> FinancialDataSet:
        extractor = MarkdownExtractor()
        raw_md = extractor.extract(config.path)

        parser = MarkdownParser()
        accounts = list(parser.parse(raw_md, period=config.period))

        return FinancialDataSet(
            company=config.company,
            cnpj=config.cnpj,
            period=config.period,
            entity_type=config.entity_type,
            source_type=SourceType.PDF,
            accounts=accounts
        )
