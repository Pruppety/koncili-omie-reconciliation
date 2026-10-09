"""Configurações centrais do pipeline, validadas via pydantic-settings.

Nenhum caminho ou parâmetro fica hardcoded nos módulos de negócio: tudo
passa por aqui para facilitar testes (basta instanciar Settings com
outros valores) e execução em ambientes diferentes (local, Docker, Airflow).
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RECONCILER_")

    # diretório de onde o comando é executado — não o local de instalação do
    # pacote, que varia entre modo dev (-e .) e instalação "real" (pip install .)
    base_dir: Path = Path.cwd()

    koncili_input_path: Path = Path("data/raw/koncili.xlsx")
    omie_input_path: Path = Path("data/raw/omie.xlsx")
    output_path: Path = Path("data/output/conciliacao_consolidada.xlsx")
    processed_db_path: Path = Path("data/processed/reconciliation.db")

    # tolerância para considerar dois valores "iguais" (arredondamento)
    valor_tolerancia: float = 0.01
    # tolerância de dias entre data Koncili e data Omie para considerar match
    data_tolerancia_dias: int = 2
    # score mínimo (0-100) do RapidFuzz para aceitar um match fuzzy
    fuzzy_score_minimo: int = 85

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.base_dir / path


settings = Settings()
