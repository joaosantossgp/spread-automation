"""Principal core mapper orchestrating Layer 1, Layer 2, and Layer 3 logic."""

from __future__ import annotations

from core.schema import SpreadSchema
from core.models import FinancialDataSet, MappingResult, SourceType
from mapping.layer1 import Layer1Matcher
from mapping.layer2 import Layer2Matcher
from mapping.layer3 import Layer3Matcher
from mapping.registry import MappingRegistry


class Mapper:
    """
    Executes mapping layers according to descending confidence principle and overriding ADRs.
    According to ADR-003, Layer 2 executes before Layer 1 to maintain output compatibility.
    Layer 3 executes for fuzzy matches (typically for PDF sources).
    """

    def __init__(self, registry: MappingRegistry):
        self._registry = registry
        self._spread_schema = SpreadSchema.load()
        self._layer1_matcher = Layer1Matcher(registry)
        self._layer2_matcher = Layer2Matcher(registry)
        self._layer3_matcher = Layer3Matcher(registry)

    def map_dataset(
        self,
        target_schema: list[dict],
        current_dataset: FinancialDataSet,
        prior_dataset: FinancialDataSet | None = None,
    ) -> list[MappingResult]:
        """
        Orchestrates mapping from a standard FinancialDataSet to a spread format schema.
        target_schema should be a list of dictionaries detailing the structure of the spread.
        """
        results: dict[int, MappingResult] = {}

        current_accounts = current_dataset.accounts
        prior_accounts = prior_dataset.accounts if prior_dataset else []

        for target in target_schema:
            row = target.get("row")
            label = target.get("label")
            prior_val = target.get("prior_value")

            if row is None or label is None:
                continue

            mapped_result = None

            # Execute Layer 2 first to preserve the ADR-defined precedence order.
            if prior_val is not None and prior_accounts:
                mapped_result = self._layer2_matcher.match_by_value(
                    target_label=label,
                    target_row=row,
                    target_prior_value=prior_val,
                    current_accounts=current_accounts,
                    prior_accounts=prior_accounts,
                )

            if mapped_result is None:
                layer1_accs = [
                    acc
                    for acc in current_accounts
                    if acc.code and self._matches_layer1_target(acc.code, row, label)
                ]

                if layer1_accs:
                    total_val = sum(acc.value for acc in layer1_accs)
                    mapped_result = MappingResult(
                        spread_row=row,
                        label=label,
                        source_account=layer1_accs[0],
                        value=total_val,
                        confidence=1.0,
                        layer=1,
                    )

            if mapped_result is None and current_dataset.source_type == SourceType.PDF:
                mapped_result = self._layer3_matcher.match_fuzzy(
                    target_label=label,
                    target_row=row,
                    target_prior_value=prior_val,
                    current_accounts=current_accounts,
                )

            if mapped_result:
                results[row] = mapped_result

        return list(results.values())

    def _matches_layer1_target(self, account_code: str, target_row: int, target_label: str) -> bool:
        mapping_target = self._registry.layer1(account_code)
        if mapping_target is None:
            return False

        # Compatibility path for registries that still map directly to visible labels.
        if mapping_target == target_label:
            return True

        schema_row = self._spread_schema.rows.get(mapping_target)
        if schema_row is None:
            return False

        if schema_row.row == target_row:
            return True

        return schema_row.label == target_label
