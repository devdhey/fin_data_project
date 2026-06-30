import os
# pyrefly: ignore [missing-import]
from curl_cffi import requests
# pyrefly: ignore [missing-import]
import duckdb
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminhos relativos inteligentes (Windows Local vs Airflow Docker)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists('/app/reports') or os.path.exists('/app/data'):
    # Modo Airflow Docker (Caminhos montados pelo seu docker-compose central)
    REPORTS_PATH = '/app/reports'
    DB_PATH = '/app/data/fin_database.duckdb'
else:
    # Modo Local Windows
    REPORTS_PATH = os.path.join(BASE_DIR, 'volumes', 'reports')
    DB_PATH = os.path.join(BASE_DIR, 'volumes', 'data', 'fin_database.duckdb')

# Mapeamento do Ticker para o Nome Completo EXATO exigido pela B3
NOME_FUNDOS_MVP = {
    'GARE11': 'GUARDIAN REAL ESTATE FUNDO DE INVESTIMENTO IMOBILIÁRIO DE RESPONSABILIDADE LIMITADA',
    'HSLG11': 'HSI LOGÍSTICA FUNDO DE INVESTIMENTO IMOBILIÁRIO DE RESP LIMITADA',
    'HGLG11': 'PÁTRIA LOG - FUNDO DE INVESTIMENTO IMOBILIÁRIO - RESPONSABILIDADE LIMITADA',
    'KNCR11': 'KINEA RENDIMENTOS IMOBILIÁRIOS FUNDO DE INVESTIMENTO IMOBILIÁRIO RESPONSABILIDADE LIMITADA',
    'MXRF11': 'MAXI RENDA FUNDO DE INVESTIMENTO IMOBILIÁRIO - FII - RESPONSABILIDADE LIMITADA'
}

def fetch_b3_fii_reports():
    os.makedirs(REPORTS_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = duckdb.connect(DB_PATH)
    
    # Criar tabelas se não existirem
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_relatorios;
        CREATE TABLE IF NOT EXISTS dim_relatorios_ativos (
            id_relatorio INTEGER DEFAULT nextval('seq_relatorios'),
            id_ativo VARCHAR,
            periodo_referencia VARCHAR,
            caminho_local_pdf VARCHAR
        );
    """)
    
    periodo = datetime.today().strftime('%Y-%m')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    import urllib.parse

    try:
        for ticker, nome_fundo in NOME_FUNDOS_MVP.items():
            logging.info(f"Buscando relatórios para {ticker} ({nome_fundo}) diretamente na API...")
            
            # Filtra APENAS pelo Nome do Fundo (Categoria 7 causa timeout no backend da B3)
            nome_encoded = urllib.parse.quote(nome_fundo)
            search_url = f"https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosDados?d=1&s=0&l=50&nomeEmissor={nome_encoded}"
            
            try:
                response = requests.get(search_url, headers=headers, timeout=30, impersonate="chrome110")
                if response.status_code != 200:
                    logging.error(f"Erro na comunicação com a B3 para {ticker}. Status: {response.status_code}")
                    continue
            except Exception as e:
                logging.error(f"Timeout/Erro ao buscar lista para {ticker}: {e}")
                continue
                
            dados = response.json().get('data', [])
            
            # Filtro adicional de segurança para garantir que é 'Relatório Gerencial'
            documentos_fundo = [
                d for d in dados 
                if ('gerencial' in str(d.get('tipoDocumento', '')).lower())
            ]
            
            if not documentos_fundo:
                logging.warning(f"Nenhum Relatório Gerencial encontrado para {ticker} ({nome_fundo}) na B3.")
                continue
                
            # Seleciona o relatório mais recente (o primeiro da lista filtrada)
            doc = documentos_fundo[0]
            doc_id = doc['id']
            data_ref = doc.get('dataReferencia', periodo).replace('/', '-')
            
            file_name = f"{ticker}_relatorio_gerencial_{doc_id}.pdf"
            file_path = os.path.join(REPORTS_PATH, file_name)
            
            if not os.path.exists(file_path):
                # O endpoint para baixar o PDF no sistema FNET (usando downloadDocumento conforme inspetoria)
                download_url = f"https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id={doc_id}"
                
                logging.info(f"Baixando PDF {doc_id} para {ticker}...")
                try:
                    pdf_response = requests.get(download_url, headers=headers, timeout=30, impersonate="chrome110")
                except Exception as e:
                    logging.error(f"Timeout/Erro ao baixar PDF de {ticker}: {e}")
                    continue
                if pdf_response.status_code == 200:
                    # Antes de salvar o novo, remove PDFs antigos desse mesmo ticker
                    for old_file in os.listdir(REPORTS_PATH):
                        if old_file.startswith(f"{ticker}_relatorio_gerencial_") and old_file != file_name:
                            old_path = os.path.join(REPORTS_PATH, old_file)
                            os.remove(old_path)
                            logging.info(f"Arquivo antigo removido: {old_file}")

                    import base64
                    
                    # A B3 retorna o PDF em formato Base64 cercado por aspas
                    content = pdf_response.content
                    if content.startswith(b'"'):
                        content = content.strip(b'"')
                    if content.startswith(b'JVBERi'): # Base64 para %PDF
                        content = base64.b64decode(content)

                    # Salva o novo arquivo
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    logging.info(f"Sucesso: Relatório de {ticker} baixado em {file_path}")
                else:
                    logging.warning(f"Erro ao baixar PDF ID {doc_id} de {ticker}.")
                    continue
            else:
                logging.info(f"Relatório {file_name} de {ticker} já existe. Pulando download.")
            
            # Persiste o metadado no DuckDB (limpando antigos para manter só o mais recente)
            query_check = f"SELECT id_relatorio FROM dim_relatorios_ativos WHERE id_ativo = '{ticker}' AND caminho_local_pdf = '{file_path}'"
            if not conn.execute(query_check).fetchone():
                # Remove registros antigos do banco
                conn.execute(f"DELETE FROM dim_relatorios_ativos WHERE id_ativo = '{ticker}'")
                
                conn.execute(f"""
                    INSERT INTO dim_relatorios_ativos (id_relatorio, id_ativo, periodo_referencia, caminho_local_pdf)
                    VALUES (nextval('seq_relatorios'), '{ticker}', '{data_ref}', '{file_path}')
                """)
                logging.info(f"Registro atualizado no DuckDB para {ticker} (antigos removidos).")
            else:
                logging.info(f"Metadados de {ticker} (ID {doc_id}) já constam no banco e são os mais atuais.")
                
    except Exception as e:
        logging.error(f"Erro no pipeline do B3 Scraper (FIIs): {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_b3_fii_reports()
