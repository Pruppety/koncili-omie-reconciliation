"""Camada de carga (load): grava o resultado consolidado.

Duas saídas, com propósitos diferentes:
- Excel formatado (.xlsx), para quem só precisa abrir e usar/filtrar.
- SQLite (data/processed), para auditoria histórica: cada execução vira
  uma linha com timestamp, permitindo responder "o que mudou desde a
  última rodada" sem reprocessar os arquivos de origem.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from loguru import logger


def export_excel(resultado: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        resultado.to_excel(writer, sheet_name="Todos", index=False)

        for status in resultado["status_match"].unique():
            aba = status[:31]  # limite de nome de aba do Excel
            resultado[resultado["status_match"] == status].to_excel(
                writer, sheet_name=aba, index=False
            )

        resumo = (
            resultado["status_match"]
            .value_counts()
            .rename_axis("status_match")
            .reset_index(name="quantidade")
        )
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

    logger.info(f"Planilha consolidada exportada para {output_path}")


def export_to_history_db(resultado: pd.DataFrame, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    execucao_em = datetime.now(UTC).isoformat()

    historico = resultado.copy()
    historico["executado_em"] = execucao_em

    with sqlite3.connect(db_path) as conn:
        historico.to_sql("reconciliacoes", conn, if_exists="append", index=False)

    logger.info(f"Histórico gravado em {db_path} (execução {execucao_em})")
