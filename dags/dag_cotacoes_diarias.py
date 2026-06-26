from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Garante que os módulos criados possam ser encontrados pelo Worker do Airflow
sys.path.append('/opt/airflow/scripts/fin_data_project')

# pyrefly: ignore [missing-import]
from loaders.db_init import init_db
# pyrefly: ignore [missing-import]
from extractors.yf_extractor import fetch_and_load_cotacoes
# pyrefly: ignore [missing-import]
from transformers.quant_engine import generate_fundamentos


default_args = {
    'owner': 'fin_data_admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'fin_data_cotacoes_diarias',
    default_args=default_args,
    description='Extração e carga de cotações diárias via yfinance (MVP)',
    schedule='0 22 * * 1-5',  # Executa às 22:00, de segunda a sexta, pós fechamento B3
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['finance', 'mvp', 'ingestion', 'duckdb'],
) as dag:

    # Task 1: Garantir que a estrutura do Banco Analítico (Tabelas) está pronta
    task_init_db = PythonOperator(
        task_id='validate_duckdb_schema',
        python_callable=init_db,
    )

    # Task 2: Executar a extração dos últimos 5 anos e aplicar Upsert no DuckDB
    task_extract_load = PythonOperator(
        task_id='extract_and_load_yf',
        python_callable=fetch_and_load_cotacoes,
        op_kwargs={'anos': 5},
    )

    # Task 3: Acionar Motor Quantitativo e Atualizar Tabela de Fundamentos
    task_quant_engine = PythonOperator(
        task_id='run_quantitative_engine',
        python_callable=generate_fundamentos,
    )

    # Definindo a hierarquia
    task_init_db >> task_extract_load >> task_quant_engine
