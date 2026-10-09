"""Interface de linha de comando do pipeline."""

from pathlib import Path

import typer
from loguru import logger

from reconciler.pipeline import run_pipeline

app = typer.Typer(help="Reconciliação automatizada entre Koncili e Omie")


@app.command()
def run(
    koncili: Path | None = typer.Option(None, help="Caminho do arquivo Koncili"),
    omie: Path | None = typer.Option(None, help="Caminho do arquivo Omie"),
    output: Path | None = typer.Option(None, help="Caminho do Excel consolidado de saída"),
):
    """Executa o pipeline completo de extração, normalização, match e exportação."""
    caminho_final = run_pipeline(koncili_path=koncili, omie_path=omie, output_path=output)
    logger.success(f"Conciliação disponível em: {caminho_final}")


if __name__ == "__main__":
    app()
