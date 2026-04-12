"""Workflow for Mode 1A (Filling an existing Spread with a single period)."""

from __future__ import annotations

from pathlib import Path

from core.schema import SpreadSchema
from core.models import EntityType
from ingestion import CVMExcelAdapter, IngestionConfig
from mapping import MappingRegistry, Mapper
from spread import SpreadReader, SpreadWriter, Highlights
from validation import ValidationReporter


class Mode1AWorkflow:
    """
    Orchestrates the entire logic flow for filling out an existing Spread Proxy
    for a given target CVM period.
    """

    def __init__(self, registry_dir: Path | None = None):
        self.registry = MappingRegistry.load(registry_dir)
        self.mapper = Mapper(self.registry)
        self.reporter = ValidationReporter()

    @staticmethod
    def detect_target_slot(
        spread_path: str | Path,
        period: str,
        *,
        start_row: int | None = None,
    ):
        """Expose normalized slot detection for UI consumers."""

        from engine.slot_detection import detect_mode1a_slot

        return detect_mode1a_slot(
            spread_path=spread_path,
            period=period,
            start_row=start_row,
        )

    def execute(
        self,
        source_path: str | Path,
        spread_path: str | Path,
        company: str,
        period: str,
        dest_col: str,
        prior_col: str | None = None,
        entity_type: EntityType = EntityType.CONSOLIDATED
    ) -> dict:
        """
        Executes Mode 1A:
        1. Ingest CVM data (assume Excel CVM template for 1A right now).
        2. Read Spread Proxy schema (with fallback prior values).
        3. Match accounts using core mapper.
        4. Overwrite targets in Spread Proxy.
        5. Apply conditional formatting highlights.
        6. Run validation checks.
        """
        source_path = Path(source_path)
        spread_path = Path(spread_path)
        spread_schema = SpreadSchema.load()
        schema_end_row = max(
            section.end_row for section in spread_schema.sections.values()
        )

        # 1. Ingest Data
        adapter = CVMExcelAdapter()
        dataset = adapter.load(
            IngestionConfig(
                path=source_path,
                company=company,
                period=period,
                entity_type=entity_type,
                # We don't strictly need prior periods here because target spread already has the heuristic columns
            )
        )

        # 2. Extract Spread Schema
        reader = SpreadReader(spread_path, sheet_name=spread_schema.sheet_name)
        target_schema = reader.extract_schema(
            label_col=spread_schema.columns.label,
            prior_val_col=prior_col,
            start_row=spread_schema.data_start_row,
            end_row=schema_end_row,
        )

        # 3. Apply Mapping Engine
        mapped_results = self.mapper.map_dataset(
            target_schema=target_schema,
            current_dataset=dataset,
            prior_dataset=None  # Mode 1A relies on the target_schema prior_values
        )

        # 4. Write output
        writer = SpreadWriter(spread_path, sheet_name=spread_schema.sheet_name)
        writer.write_results(dest_col=dest_col, results=mapped_results, overwrite=True)

        # 5. Apply graphical highlights
        highlights = Highlights(spread_path, sheet_name=spread_schema.sheet_name)
        highlights.apply_styles(col=dest_col, results=mapped_results)

        # 6. Validate
        report = self.reporter.report(schema_targets=target_schema, mapped_results=mapped_results)

        return {
            "status": "success",
            "mapped_count": len(mapped_results),
            "validation": {
                "is_valid": report.is_valid,
                "missing": report.missing_labels,
                "discrepancy": str(report.discrepancy)
            }
        }
