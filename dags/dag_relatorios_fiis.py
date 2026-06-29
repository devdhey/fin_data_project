from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Mapeamento do caminho compartilhado dentro da infraestrutura central de Airflow
sys.path.append('/opt/airflow/scripts/fin_data_project/scripts')

# pyrefly: ignore [missing-import]
from loaders.db_init import init_db
# pyrefly: ignore [missing-import]
from extractors.b3_fii_scraper import fetch_b3_fii_reports

default_args = {
    'owner': 'fin_data_admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    'fin_data_relatorios_fiis_b3',
    default_args=default_args,
    description='Pipeline de coleta mensal de Relatórios Gerenciais (FIIs - B3)',
    schedule='0 18 * * 5',  # Executa toda Sexta-feira às 18:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['finance', 'mvp', 'b3', 'fiis', 'documents'],
) as dag:

    # Task 1: Validar Banco e Dimensões
    task_init_db = PythonOperator(
        task_id='validate_duckdb_schema',
        python_callable=init_db,
    )

    # Task 2: Executar coleta FIIs B3
    task_scrape_b3 = PythonOperator(
        task_id='scrape_and_catalog_b3_reports',
        python_callable=fetch_b3_fii_reports,
    )

    # Sequenciamento Lógico
    task_init_db >> task_scrape_b3
