import os
import requests
import duckdb
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REPORTS_PATH = '/app/reports'
DB_PATH = '/app/data/fin_database.duckdb'
FIIS_MVP = ['GARE11', 'HSLG11', 'HGLG11', 'KNCR11', 'MXRF11']

def fetch_b3_fii_reports():
    """
    Realiza a coleta de Relatórios Gerenciais Mensais para Fundos Imobiliários da B3 (Sistema Fundos.net).
    Para MVP, empregamos a mesma técnica de placeholder do CVM Scraper, assegurando que o I/O
    de PDFs e o cruzamento relacional na fato funcione. Em produção exigiria parser de frames do site da B3.
    """
    os.makedirs(REPORTS_PATH, exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    
    # PDF genérico usado como *mock* de relatório
    dummy_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    # FIIs reportam mensalmente, a indexação do período segue o padrão Ano-Mês (ex: 2024-05)
    periodo = datetime.today().strftime('%Y-%m')
    
    try:
        for ticker in FIIS_MVP:
            logging.info(f"Monitorando novos Relatórios Gerenciais para o FII {ticker}...")
            
            # Formatação do nome de arquivo padronizado
            file_name = f"{ticker}_relatorio_gerencial_{periodo}.pdf"
            file_path = os.path.join(REPORTS_PATH, file_name)
            
            # 1. Checagem de arquivo (Evita I/O e tráfego de rede)
            if not os.path.exists(file_path):
                response = requests.get(dummy_pdf_url, timeout=15)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    logging.info(f"Relatório de {ticker} baixado com sucesso em: {file_path}")
                else:
                    logging.warning(f"Erro na comunicação HTTP ao buscar documento de {ticker}.")
                    continue
            else:
                logging.info(f"Arquivo já contido na biblioteca local: {file_path}. Pulo sistêmico efetuado.")
            
            # 2. Persistência de metadata no Data Warehouse (Idempotência no Banco)
            query_check = f"SELECT id_relatorio FROM dim_relatorios_ativos WHERE id_ativo = '{ticker}' AND periodo_referencia = '{periodo}'"
            check = conn.execute(query_check).fetchone()
            
            if not check:
                max_id = conn.execute("SELECT MAX(id_relatorio) FROM dim_relatorios_ativos").fetchone()[0]
                next_id = 1 if max_id is None else int(max_id) + 1
                
                conn.execute(f"""
                    INSERT INTO dim_relatorios_ativos (id_relatorio, id_ativo, periodo_referencia, caminho_local_pdf)
                    VALUES ({next_id}, '{ticker}', '{periodo}', '{file_path}')
                """)
                logging.info(f"Vínculo do Relatório ({ticker}) criado no DuckDB sob o ID #{next_id}.")
            else:
                logging.info(f"Apontamento de PDF para {ticker} em {periodo} já está validado no banco.")
                
    except Exception as e:
        logging.error(f"Erro no pipeline do B3 Scraper (FIIs): {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_b3_fii_reports()
