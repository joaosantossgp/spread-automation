"""Regression tests for Mode 1A."""

import json
import re
import shutil
from pathlib import Path
from engine.workflow_1a import Mode1AWorkflow
from tests.conftest import DATA_DIR

GOLDEN_REF_FILE = Path(__file__).parent / "golden_refs.json"

def _ensure_golden_reference(minerva_4t24):
    """
    Checks if the golden reference JSON exists. If not, dynamically generates it
    by executing the legacy pipeline on the provided dataset copies.
    """
    if GOLDEN_REF_FILE.exists():
        with open(GOLDEN_REF_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "minerva_4t24" in data:
                return data["minerva_4t24"]

    print("\n[Golden Ref] Computing golden reference dynamically via legacy pipeline...")
    from processing.pipeline import processar

    logs = []
    def capture_log(msg):
        logs.append(str(msg))

    try:
        processar(
            ori=Path(minerva_4t24["dados_path"]),
            spr=Path(minerva_4t24["spread_path"]),
            tipo="consolidado",
            periodo="4T24",
            src_txt="D",
            dst_txt="L",
            start_row=27,
            out_dir=None,
            log=capture_log
        )
    except Exception as e:
        raise RuntimeError(f"Legacy pipeline failed to generate golden reference: {e}")

    mapped_count = 0
    for line in logs:
        match = re.search(r"Valores correspondidos:\s*(\d+)", line)
        if match:
            mapped_count = int(match.group(1))

    if mapped_count == 0:
        raise ValueError("Golden reference generated 0 matched accounts. Is the fixture corrupted?")

    data = {}
    if GOLDEN_REF_FILE.exists():
        try:
            with open(GOLDEN_REF_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    data["minerva_4t24"] = {"mapped_count": mapped_count}
    
    with open(GOLDEN_REF_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data["minerva_4t24"]

def test_mode1a_matches_legacy_mapped_count(minerva_4t24):
    """
    Validates that Mode1AWorkflow processes the exact same number of matched accounts
    as the legacy processar() pipeline.
    """
    # 1. Establish or read golden baseline
    golden = _ensure_golden_reference(minerva_4t24)

    # 2. Restore pristine copies of the spreadsheets for Mode 1A,
    # because the legacy pipeline modified the minerva_4t24 spreadsheet in-place!
    original_dados = DATA_DIR / "Minerva 4T24" / "DadosDocumento.xlsx"
    original_spread = DATA_DIR / "Minerva 4T24" / "Spread Proxy.xlsx"
    
    shutil.copy(original_dados, minerva_4t24["dados_path"])
    shutil.copy(original_spread, minerva_4t24["spread_path"])

    # 3. Process with Mode 1A workflow
    workflow = Mode1AWorkflow()
    result = workflow.execute(
        source_path=minerva_4t24["dados_path"],
        spread_path=minerva_4t24["spread_path"],
        company="Minerva",
        period="4T24",
        prior_col="D",
        dest_col="L"
    )

    assert isinstance(result, dict)
    assert result["status"] == "success"
    
    mode1a_count = result["mapped_count"]
    legacy_count = golden["mapped_count"]
    
    # 4. Compare counts
    assert mode1a_count == legacy_count, f"Mode 1A mapped {mode1a_count} items, expected {legacy_count} (golden reference)"

def test_mode1a_individual(minerva_4t24):
    """
    Validates that Mode1AWorkflow processes the Individual scenario without crashing
    and maps some accounts.
    """
    workflow = Mode1AWorkflow()
    result = workflow.execute(
        source_path=minerva_4t24["dados_path"],
        spread_path=minerva_4t24["spread_path"],
        company="Minerva",
        period="4T24",
        prior_col="D",
        dest_col="L",
        entity_type="individual"
    )

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["mapped_count"] > 0


def test_mode1a_missing_entity_type(minerva_4t24):
    """
    Validates that omitting entity_type or passing an invalid one raises a ValueError
    or is handled gracefully, but we test invalid/missing behavior in adapter directly.
    """
    import pytest
    from core.models import EntityType

    # Wait, workflow defaults to CONSOLIDATED. If we pass None or an invalid type explicitly:
    workflow = Mode1AWorkflow()
    with pytest.raises(ValueError, match="Expected one of"):
        workflow.execute(
            source_path=minerva_4t24["dados_path"],
            spread_path=minerva_4t24["spread_path"],
            company="Minerva",
            period="4T24",
            prior_col="D",
            dest_col="L",
            entity_type="invalid_type"
        )
