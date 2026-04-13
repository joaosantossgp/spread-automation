"""Workflow for Mode 2A (PDF → existing Spread Proxy)."""

from __future__ import annotations

from pathlib import Path

from core.schema import SpreadSchema
from core.models import EntityType, SourceType
from ingestion import IngestionConfig
from ingestion.pdf_adapter import PDFAdapter
from mapping import MappingRegistry, Mapper
from spread import SpreadReader, SpreadWriter, Highlights
from validation import ValidationReporter

_AUTO_THRESHOLD = 0.95
_REVIEW_THRESHOLD = 0.60


class Workflow2A:
    """
    Orchestrates Mode 2A: extract financial data from a PDF and write it
    into an *existing* Spread Proxy, classifying each result by confidence.

    Returns a dict with three buckets:
        - "auto"           → accepted automatically (confidence >= 0.95)
        - "pending_review" → requires human review   (0.60 <= confidence < 0.95)
        - "rejected"       → below minimum threshold (confidence < 0.60)
    """

    def __init__(self, registry_dir: Path | None = None):
        self.registry = MappingRegistry.load(registry_dir)
        self.mapper = Mapper(self.registry)
        self.reporter = ValidationReporter()

    def execute(
        self,
        pdf_path: str | Path,
        spread_path: str | Path,
        company: str,
        period: str,
        dest_col: str,
        prior_col: str | None = None,
        entity_type: EntityType = EntityType.CONSOLIDATED,
    ) -> dict:
        """
        Execute Mode 2A.

        1. Ingest PDF into a FinancialDataSet (Layer 3 fuzzy matching).
        2. Detect scanned-only PDFs (no text) and reject early.
        3. Extract Spread schema from the existing Spread Proxy.
        4. Map accounts using Mapper (Layer 2 → Layer 1 → Layer 3).
        5. Write auto-accepted results to the Spread Proxy.
        6. Apply highlights and produce validation report.
        7. Return stratified result buckets.
        """
        pdf_path = Path(pdf_path)
        spread_path = Path(spread_path)

        # 1. Ingest PDF
        adapter = PDFAdapter()
        config = IngestionConfig(
            path=pdf_path,
            company=company,
            period=period,
            entity_type=entity_type,
        )
        try:
            dataset = adapter.load(config)
        except Exception as exc:
            # Surface scanned/image-only PDFs with a clear rejection message
            raise ValueError(
                f"PDF ingestion failed for '{pdf_path.name}'. "
                "The file may be image-only (scanned) and contain no extractable text. "
                f"Original error: {exc}"
            ) from exc

        if not dataset.accounts:
            raise ValueError(
                f"No financial accounts extracted from '{pdf_path.name}'. "
                "The PDF may be scanned/image-only or have an unsupported format."
            )

        # 2. Extract Spread schema
        spread_schema = SpreadSchema.load()
        schema_end_row = max(
            section.end_row for section in spread_schema.sections.values()
        )
        reader = SpreadReader(spread_path, sheet_name=spread_schema.sheet_name)
        target_schema = reader.extract_schema(
            label_col=spread_schema.columns.label,
            prior_val_col=prior_col,
            start_row=spread_schema.data_start_row,
            end_row=schema_end_row,
        )

        # 3. Map accounts
        mapped_results = self.mapper.map_dataset(
            target_schema=target_schema,
            current_dataset=dataset,
        )

        # 4. Stratify by confidence
        auto = [r for r in mapped_results if r.confidence >= _AUTO_THRESHOLD]
        pending_review = [
            r for r in mapped_results
            if _REVIEW_THRESHOLD <= r.confidence < _AUTO_THRESHOLD
        ]
        rejected = [r for r in mapped_results if r.confidence < _REVIEW_THRESHOLD]

        # 5. Write only auto-accepted results to the Spread Proxy
        writer = SpreadWriter(spread_path, sheet_name=spread_schema.sheet_name)
        writer.write_results(dest_col=dest_col, results=auto, overwrite=True)

        # 6. Highlights for auto-accepted results only
        highlights = Highlights(spread_path, sheet_name=spread_schema.sheet_name)
        highlights.apply_styles(col=dest_col, results=auto)

        # 7. Validate and build report
        report = self.reporter.report(
            schema_targets=target_schema,
            mapped_results=auto,
        )

        return {
            "status": "success",
            "source_type": SourceType.PDF.value,
            "auto": [_serialise_result(r) for r in auto],
            "pending_review": [_serialise_result(r) for r in pending_review],
            "rejected": [_serialise_result(r) for r in rejected],
            "validation": {
                "is_valid": report.is_valid,
                "missing": report.missing_labels,
                "discrepancy": str(report.discrepancy),
            },
        }


def _serialise_result(result) -> dict:
    """Convert a MappingResult to a JSON-safe dict."""
    return {
        "spread_row": result.spread_row,
        "label": result.label,
        "value": str(result.value) if result.value is not None else None,
        "confidence": result.confidence,
        "layer": result.layer,
        "source_account_code": (
            result.source_account.code if result.source_account else None
        ),
        "source_account_description": (
            result.source_account.description if result.source_account else None
        ),
    }
