import os
import requests
# pyrefly: ignore [missing-import]
import duckdb
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminhos relativos inteligentes (Windows Local vs Airflow Docker)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists('/app/reports') or os.path.exists('/app/data'):
    REPORTS_PATH = '/app/reports'
    DB_PATH = '/app/data/fin_database.duckdb'
else:
    REPORTS_PATH = os.path.join(BASE_DIR, 'volumes', 'reports')
    DB_PATH = os.path.join(BASE_DIR, 'volumes', 'data', 'fin_database.duckdb')
ACOES_MVP = [
    'BBAS3', 'EGIE3', 'CXSE3', 'TAEE4', 'FIQE3',
    'ABCB4', 'BBSE3'
]

def fetch_cvm_reports():
    """
    Realiza a extração de balanços em PDF (DFP/ITR) das empresas de capital aberto (CVM).
    Para fins de estabilidade do MVP sem a necessidade de instanciar WebDrivers pesados 
    (Selenium) na infraestrutura atual, efetuamos o mock processual baixando relatórios
    placeholders em PDF. O foco principal é validar a robustez de I/O de arquivos 
    (Volume reports_vol) e o cruzamento dos metadados no DuckDB.
    """
    os.makedirs(REPORTS_PATH, exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    
    # URL pública estável de um PDF genérico para homologar o volume Docker e visualização no Superset
    dummy_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    # Formata período dinamicamente (ex: 2024-Q1)
    trimestre = (datetime.today().month - 1) // 3 + 1
    periodo = f"{datetime.today().year}-Q{trimestre}"
    
    try:
        for ticker in ACOES_MVP:
            logging.info(f"Localizando demonstrações (DFP/ITR) da CVM para o ativo {ticker}...")
            
            # Padronização do arquivo de saída
            file_name = f"{ticker}_balanco_{periodo}.pdf"
            file_path = os.path.join(REPORTS_PATH, file_name)
            
            # Idempotência de Download (evita recarregar na rede e disco se já possui o documento)
            if not os.path.exists(file_path):
                response = requests.get(dummy_pdf_url, timeout=15)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    logging.info(f"Download do PDF concluído. Armazenado no diretório base: {file_path}")
                else:
                    logging.warning(f"Portal indisponível ao baixar relatório corporativo para {ticker}.")
                    continue
            else:
                logging.info(f"Arquivo já indexado localmente: {file_path}. Pulando etapa de download.")
            
            # Registrar metadados em dim_relatorios_ativos no Data Warehouse
            # Regra Idempotente: Verifica existência
            query_check = f"SELECT id_relatorio FROM dim_relatorios_ativos WHERE id_ativo = '{ticker}' AND periodo_referencia = '{periodo}'"
            check = conn.execute(query_check).fetchone()
            
            if not check:
                # Simulação manual de auto_increment para IDs devido à complexidade leve
                max_id = conn.execute("SELECT MAX(id_relatorio) FROM dim_relatorios_ativos").fetchone()[0]
                next_id = 1 if max_id is None else int(max_id) + 1
                
                conn.execute(f"""
                    INSERT INTO dim_relatorios_ativos (id_relatorio, id_ativo, periodo_referencia, caminho_local_pdf)
                    VALUES ({next_id}, '{ticker}', '{periodo}', '{file_path}')
                """)
                logging.info(f"Metadado de {ticker} enraizado no DuckDB. Referência ID {next_id}.")
            else:
                logging.info(f"Metadado contábil de {ticker} referente a {periodo} já consta na arquitetura analítica.")
                
    except Exception as e:
        logging.error(f"Erro crítico no pipeline CVM Scraping: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_cvm_reports()
