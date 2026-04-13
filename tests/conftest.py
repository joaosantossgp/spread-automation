"""Pytest fixtures and configuration."""

import shutil
from pathlib import Path
import pytest

DATA_DIR = Path(__file__).parent.parent / "data"

@pytest.fixture
def minerva_4t24(tmp_path):
    """
    Fixture that provides isolated copies of Minerva 4T24 test data.
    Skips the test if the binary data directory is missing.
    """
    minerva_dir = DATA_DIR / "Minerva 4T24"
    if not minerva_dir.exists():
        pytest.skip(f"Test fixture directory {minerva_dir.absolute()} is missing.")

    src_dados = minerva_dir / "DadosDocumento.xlsx"
    src_spread = minerva_dir / "Spread Proxy.xlsx"

    if not src_dados.exists() or not src_spread.exists():
        pytest.skip(f"Required binary Excel files missing inside {minerva_dir}.")

    # Copy to tmp_path to prevent tests from modifying tracked/untracked state
    tmp_dados = tmp_path / "DadosDocumento.xlsx"
    tmp_spread = tmp_path / "Spread Proxy.xlsx"

    shutil.copy(src_dados, tmp_dados)
    shutil.copy(src_spread, tmp_spread)

    return {
        "dados_path": tmp_dados,
        "spread_path": tmp_spread,
    }
