"""Workflow for Mode 1A (Filling an existing Spread with a single period)."""

from __future__ import annotations

from pathlib import Path

from core.schema import SpreadSchema
from core.models import EntityType, FinancialDataSet
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
        dest_col: str | None = None,
        prior_col: str | None = None,
        entity_type: EntityType = EntityType.CONSOLIDATED,
        multi_period: bool = False,
    ) -> dict | list[dict]:
        """
        Executes Mode 1A:
        If missing, slot detection determines the target columns automatically.
        If multi_period is True, it processes the prior period first and then the current,
        re-reading the target Spread schema in sequence.
        """
        if dest_col is None or prior_col is None:
            slot = self.detect_target_slot(spread_path, period)
            if not slot.has_available_slot:
                raise ValueError(f"No available slot detected in the spread grid. {slot.message}")
            dest_col = dest_col or slot.destination_column
            prior_col = prior_col or slot.source_column

        if multi_period:
            return self._execute_multi(
                source_path=source_path,
                spread_path=spread_path,
                company=company,
                period=period,
                start_prior_col=prior_col,
                start_dest_col=dest_col,
                entity_type=entity_type,
            )

        # Single period path
        adapter = CVMExcelAdapter()
        dataset = adapter.load(
            IngestionConfig(
                path=source_path,
                company=company,
                period=period,
                entity_type=entity_type,
            )
        )
        return self._execute_single_run(
            spread_path=spread_path,
            dataset=dataset,
            dest_col=dest_col,
            prior_col=prior_col,
        )

    def _execute_multi(
        self,
        source_path: str | Path,
        spread_path: str | Path,
        company: str,
        period: str,
        start_prior_col: str,
        start_dest_col: str,
        entity_type: EntityType,
    ) -> list[dict]:
        from core.utils import periodos
        from processing.runtime_bridge import next_data_column

        # Identify the periods
        atual, ant, ant2, is_trim = periodos(period)
        
        # 1. Ingest Data once, retrieving both the prior period and the current period
        source_path = Path(source_path)
        adapter = CVMExcelAdapter()
        dataset = adapter.load(
            IngestionConfig(
                path=source_path,
                company=company,
                period=atual,
                previous_period=ant,
                entity_type=entity_type,
            )
        )
        
        # Determine the two periods to process. We sequence the prior (ant) first, then current (atual)
        periodos_lista = [ant, atual]
        
        results = []
        current_prior_col = start_prior_col
        current_dest_col = start_dest_col
        
        for per in periodos_lista:
            # Filter dataset for the specific period's accounts
            period_accounts = [acc for acc in dataset.accounts if acc.period == per]
            if not period_accounts:
                raise ValueError(f"No accounts found for period {per} in source dataset.")
                
            filtered_dataset = FinancialDataSet(
                company=dataset.company,
                cnpj=dataset.cnpj,
                period=per,
                entity_type=dataset.entity_type,
                source_type=dataset.source_type,
                accounts=period_accounts
            )
            
            res = self._execute_single_run(
                spread_path=spread_path,
                dataset=filtered_dataset,
                dest_col=current_dest_col,
                prior_col=current_prior_col
            )
            res["period"] = per
            results.append(res)
            
            # For the next run, the newly written column becomes the prior column
            current_prior_col = current_dest_col
            _, _, _, per_is_trim = periodos(per)
            current_dest_col = next_data_column(current_dest_col, include_quarterly=per_is_trim)
            
        return results

    def _execute_single_run(
        self,
        spread_path: str | Path,
        dataset: FinancialDataSet,
        dest_col: str,
        prior_col: str | None,
    ) -> dict:
        spread_path = Path(spread_path)
        spread_schema = SpreadSchema.load()
        schema_end_row = max(
            section.end_row for section in spread_schema.sections.values()
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
