import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pandas as pd

from ingestion.base import IngestionConfig
from ingestion.excel_adapter import CVMExcelAdapter
from core.models import EntityType, SourceType


def test_excel_adapter_validation_missing_entity_type():
    adapter = CVMExcelAdapter()
    config = IngestionConfig(
        path="dummy.xlsx",
        company="Dummy Co",
        period="1T23",
        entity_type=None  # Explicitly invalid
    )

    with pytest.raises(ValueError) as exc:
        adapter.load(config)

    assert "Invalid or missing entity_type" in str(exc.value)


def test_excel_adapter_validation_invalid_entity_type():
    adapter = CVMExcelAdapter()
    config = IngestionConfig(
        path="dummy.xlsx",
        company="Dummy Co",
        period="1T23",
        entity_type="NOT_AN_ENTITY"  # Explicitly invalid
    )

    with pytest.raises(ValueError) as exc:
        adapter.load(config)

    assert "Invalid or missing entity_type" in str(exc.value)


@patch("pandas.read_excel")
@patch("pandas.ExcelFile")
def test_excel_adapter_dmpl_consolidated(mock_excel_file, mock_read_excel):
    # Setup mock Excel file
    mock_xls = MagicMock()
    mock_xls.sheet_names = ["DF Cons DMPL Atual"]
    mock_excel_file.return_value = mock_xls

    # Setup mock DataFrame for DMPL
    # For Consolidated, it should look for 'Patrimonio liquido Consolidado'
    mock_df = pd.DataFrame({
        "Codigo Conta": ["1", "2"],
        "Descricao Conta": ["Account 1", "Account 2"],
        "Patrimonio liquido Consolidado": [100.0, 200.0],
        "Patrimonio Liquido": [10.0, 20.0]  # This should be ignored
    })
    mock_read_excel.return_value = mock_df

    adapter = CVMExcelAdapter()
    config = IngestionConfig(
        path="dummy.xlsx",
        company="Dummy Co",
        period="1T23",
        entity_type=EntityType.CONSOLIDATED
    )

    dataset = adapter.load(config)

    assert len(dataset.accounts) == 2
    assert dataset.accounts[0].value == Decimal("100")
    assert dataset.accounts[1].value == Decimal("200")


@patch("pandas.read_excel")
@patch("pandas.ExcelFile")
def test_excel_adapter_dmpl_individual(mock_excel_file, mock_read_excel):
    # Setup mock Excel file
    mock_xls = MagicMock()
    mock_xls.sheet_names = ["DF Ind DMPL Atual"]
    mock_excel_file.return_value = mock_xls

    # Setup mock DataFrame for DMPL
    # For Individual, it should look for 'Patrimonio Liquido'
    mock_df = pd.DataFrame({
        "Codigo Conta": ["1", "2"],
        "Descricao Conta": ["Account 1", "Account 2"],
        "Patrimonio liquido Consolidado": [100.0, 200.0],  # This should be ignored
        "Patrimonio Liquido": [10.0, 20.0]
    })
    mock_read_excel.return_value = mock_df

    adapter = CVMExcelAdapter()
    config = IngestionConfig(
        path="dummy.xlsx",
        company="Dummy Co",
        period="1T23",
        entity_type=EntityType.INDIVIDUAL
    )

    dataset = adapter.load(config)

    assert len(dataset.accounts) == 2
    assert dataset.accounts[0].value == Decimal("10")
    assert dataset.accounts[1].value == Decimal("20")
