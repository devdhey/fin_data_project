from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Mapeamento do caminho compartilhado dentro da infraestrutura central de Airflow
sys.path.append('/opt/airflow/scripts/fin_data_project')

# pyrefly: ignore [missing-import]
from loaders.db_init import init_db
# pyrefly: ignore [missing-import]
from extractors.cvm_scraper import fetch_cvm_reports


default_args = {
    'owner': 'fin_data_admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10), # Portal RAD CVM pode ser instável, delay alto de repetição
}

with DAG(
    'fin_data_balancos_acoes_cvm',
    default_args=default_args,
    description='Pipeline de coleta automatizada de Balanços Trimestrais (Ações - CVM)',
    schedule='0 20 * * 5',  # Execução agendada para as Sextas-feiras às 20h
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['finance', 'mvp', 'cvm', 'documents'],
) as dag:

    # Task 1: Garantir que a tabela dimensões e o banco DuckDB existem
    task_init_db = PythonOperator(
        task_id='validate_duckdb_schema',
        python_callable=init_db,
    )

    # Task 2: Raspar, baixar os PDFs e persistir caminhos no DuckDB
    task_scrape_cvm = PythonOperator(
        task_id='scrape_and_catalog_cvm_reports',
        python_callable=fetch_cvm_reports,
    )

    # Sequenciamento Lógico
    task_init_db >> task_scrape_cvm
