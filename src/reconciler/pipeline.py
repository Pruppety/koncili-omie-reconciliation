"""Orquestração do pipeline — ponto único usado tanto pela CLI quanto pela DAG do Airflow.

Mantendo essa função livre de qualquer detalhe de Typer ou Airflow, o
mesmo código roda local, em container ou agendado, sem duplicação.
"""

from pathlib import Path

from loguru import logger

from reconciler.config import settings
from reconciler.export import export_excel, export_to_history_db
from reconciler.extract import extract_koncili, extract_omie
from reconciler.match import reconciliar
from reconciler.transform import normalize_koncili, normalize_omie


def run_pipeline(
    koncili_path: Path | None = None,
    omie_path: Path | None = None,
    output_path: Path | None = None,
    db_path: Path | None = None,
) -> Path:
    koncili_path = settings.resolve(koncili_path or settings.koncili_input_path)
    omie_path = settings.resolve(omie_path or settings.omie_input_path)
    output_path = settings.resolve(output_path or settings.output_path)
    db_path = settings.resolve(db_path or settings.processed_db_path)

    logger.info("Iniciando pipeline de reconciliação Koncili x Omie")

    koncili_raw = extract_koncili(koncili_path)
    omie_raw = extract_omie(omie_path)

    koncili = normalize_koncili(koncili_raw)
    omie = normalize_omie(omie_raw)

    resultado = reconciliar(koncili, omie)

    export_excel(resultado, output_path)
    export_to_history_db(resultado, db_path)

    total_divergente = (resultado["status_match"] != "CONCILIADO").sum()
    if total_divergente:
        logger.warning(
            f"{total_divergente} lançamentos precisam de atenção "
            f"(divergentes ou sem par encontrado)"
        )

    logger.info("Pipeline concluído com sucesso")
    return output_path


if __name__ == "__main__":
    run_pipeline()
