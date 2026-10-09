"""DAG do Airflow para o pipeline de reconciliação Koncili x Omie.

Por que Airflow aqui: retries automáticos em caso de falha momentânea
de leitura, histórico visual de execuções, e agendamento declarativo
(roda todo dia às 7h, por exemplo) sem precisar de um cron externo
nem de lógica de retry escrita à mão.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _run_pipeline():
    # import tardio para que o parsing da DAG não dependa de todas as
    # libs do pipeline estarem instaladas no scheduler
    from reconciler.pipeline import run_pipeline

    run_pipeline()


with DAG(
    dag_id="koncili_omie_reconciliation",
    description="Extrai, normaliza, concilia e exporta Koncili x Omie",
    default_args=default_args,
    schedule="0 7 * * *",  # todos os dias às 07:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["financeiro", "reconciliacao"],
) as dag:
    reconciliar_task = PythonOperator(
        task_id="run_reconciliation_pipeline",
        python_callable=_run_pipeline,
    )
