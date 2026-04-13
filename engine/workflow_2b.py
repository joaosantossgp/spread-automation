"""Workflow for Mode 2B (PDF → blank Spread template)."""

from __future__ import annotations

import shutil
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


class Workflow2B:
    """
    Orchestrates Mode 2B: extract financial data from a PDF and write it
    into a *blank* Spread template (provided or auto-located).

    Copies the template to dest_path before writing, so the template is
    never modified in-place.

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
        dest_path: str | Path,
        company: str,
        period: str,
        dest_col: str,
        prior_col: str | None = None,
        entity_type: EntityType = EntityType.CONSOLIDATED,
        template_path: str | Path | None = None,
    ) -> dict:
        """
        Execute Mode 2B.

        1. Copy blank template to dest_path (so the template stays pristine).
        2. Ingest PDF; detect scanned-only PDFs and reject early.
        3. Extract Spread schema from the newly copied spread.
        4. Map accounts using Mapper (Layer 2 → Layer 1 → Layer 3).
        5. Write auto-accepted results to dest_path.
        6. Apply highlights and produce validation report.
        7. Return stratified result buckets.
        """
        pdf_path = Path(pdf_path)
        dest_path = Path(dest_path)

        # 1. Copy blank template to dest_path
        if template_path is not None:
            src_template = Path(template_path)
        else:
            spread_schema = SpreadSchema.load()
            src_template = spread_schema.blank_template_path
            if not isinstance(src_template, Path):
                src_template = Path(src_template)

        if not src_template.exists():
            raise FileNotFoundError(
                f"Blank Spread template not found at '{src_template}'. "
                "Provide an explicit template_path or configure SpreadSchema.blank_template_path."
            )

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_template, dest_path)

        # 2. Ingest PDF
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

        # 3. Extract schema from the freshly-copied spread
        spread_schema = SpreadSchema.load()
        schema_end_row = max(
            section.end_row for section in spread_schema.sections.values()
        )
        reader = SpreadReader(dest_path, sheet_name=spread_schema.sheet_name)
        target_schema = reader.extract_schema(
            label_col=spread_schema.columns.label,
            prior_val_col=prior_col,
            start_row=spread_schema.data_start_row,
            end_row=schema_end_row,
        )

        # 4. Map accounts
        mapped_results = self.mapper.map_dataset(
            target_schema=target_schema,
            current_dataset=dataset,
        )

        # 5. Stratify by confidence
        auto = [r for r in mapped_results if r.confidence >= _AUTO_THRESHOLD]
        pending_review = [
            r for r in mapped_results
            if _REVIEW_THRESHOLD <= r.confidence < _AUTO_THRESHOLD
        ]
        rejected = [r for r in mapped_results if r.confidence < _REVIEW_THRESHOLD]

        # 6. Write only auto-accepted results to the destination spread
        writer = SpreadWriter(dest_path, sheet_name=spread_schema.sheet_name)
        writer.write_results(dest_col=dest_col, results=auto, overwrite=True)

        # 7. Highlights for auto-accepted results
        highlights = Highlights(dest_path, sheet_name=spread_schema.sheet_name)
        highlights.apply_styles(col=dest_col, results=auto)

        # 8. Validate and build report
        report = self.reporter.report(
            schema_targets=target_schema,
            mapped_results=auto,
        )

        return {
            "status": "success",
            "source_type": SourceType.PDF.value,
            "output_path": str(dest_path),
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
