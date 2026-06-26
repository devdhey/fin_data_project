from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Mapeamento do caminho compartilhado dentro da infraestrutura central de Airflow
sys.path.append('/opt/airflow/scripts/fin_data_project')

from transformers.data_quality import run_data_quality_checks

default_args = {
    'owner': 'fin_data_admin',
    'depends_on_past': False,
    'email_on_failure': False, # Em produção, alterar para alertar time de Engenharia
    'email_on_retry': False,
    'retries': 0, # Zero retries: Se os dados estão corrompidos, queremos a falha exposta imediatamente.
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'fin_data_auditoria_qualidade_dados',
    default_args=default_args,
    description='Pipeline Noturno de Auditoria e Data Quality do Banco Analítico',
    schedule='0 23 * * 1-5',  # Executa de segunda a sexta, às 23h (Sempre depois do pipeline de Cotações)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['finance', 'mvp', 'data-quality', 'duckdb'],
) as dag:

    # Única Task: Executar Testes de Rigor Analítico
    task_dq_audit = PythonOperator(
        task_id='run_dq_audit_checks',
        python_callable=run_data_quality_checks,
    )

    task_dq_audit
