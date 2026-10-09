import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from generate_fake_data import gerar_dados

from reconciler.pipeline import run_pipeline


def test_pipeline_ponta_a_ponta_com_dados_sinteticos(tmp_path):
    raw_dir = tmp_path / "raw"
    gerar_dados(raw_dir)

    output_path = tmp_path / "output" / "consolidado.xlsx"
    db_path = tmp_path / "processed" / "reconciliation.db"

    caminho_final = run_pipeline(
        koncili_path=raw_dir / "koncili.xlsx",
        omie_path=raw_dir / "omie.xlsx",
        output_path=output_path,
        db_path=db_path,
    )

    assert caminho_final.exists()

    resumo = pd.read_excel(caminho_final, sheet_name="Resumo")
    assert "status_match" in resumo.columns
    assert resumo["quantidade"].sum() > 0

    todos = pd.read_excel(caminho_final, sheet_name="Todos")
    assert {"CONCILIADO", "SOMENTE_KONCILI", "SOMENTE_OMIE"}.issubset(
        set(todos["status_match"].unique())
    )
