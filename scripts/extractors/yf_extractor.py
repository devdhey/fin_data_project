import yfinance as yf
import pandas as pd
import duckdb
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminhos orientados ao contêiner (mapeados nos volumes do Airflow)
RAW_PATH = '/app/data/raw'
DB_PATH = '/app/data/fin_database.duckdb'

# Escopo Real (15 ativos da carteira)
ATIVOS_MVP = [
    'BBAS3.SA', 'EGIE3.SA', 'CXSE3.SA', 'ITUB4.SA', 'VALE3.SA', 
    'PETR4.SA', 'WEGE3.SA', 'TAEE11.SA', 'BBDC4.SA', 'VIVT3.SA',
    'GARE11.SA', 'HSLG11.SA', 'HGLG11.SA', 'KNCR11.SA', 'MXRF11.SA'
]

def fetch_and_load_cotacoes(anos=5):
    os.makedirs(RAW_PATH, exist_ok=True)
    dfs = []
    
    data_inicio = (datetime.today() - timedelta(days=365*anos)).strftime('%Y-%m-%d')
    
    for ticker in ATIVOS_MVP:
        logging.info(f"Buscando histórico ({anos} anos) para: {ticker}")
        try:
            ativo = yf.Ticker(ticker)
            df = ativo.history(start=data_inicio, interval="1d")
            
            if df.empty:
                logging.warning(f"Nenhum dado encontrado para {ticker}.")
                continue
                
            # Limpeza do dataframe retornado pelo yfinance
            df.reset_index(inplace=True)
            # Remove fuso horário se existir (ex: timezone do yfinance)
            if df['Date'].dt.tz is not None:
                df['Date'] = df['Date'].dt.tz_localize(None)
            
            df['Date'] = df['Date'].dt.date
            
            # Padroniza nomes das colunas e os identificadores dos ativos (removendo .SA)
            df_cleaned = pd.DataFrame({
                'data_pregao': df['Date'],
                'id_ativo': ticker.replace('.SA', ''),
                'preco_fechamento': df['Close'].round(2)
            })
            
            dfs.append(df_cleaned)
            logging.info(f"Sucesso: {len(df_cleaned)} registros recuperados para {ticker}.")
            
        except Exception as e:
            logging.error(f"Erro ao extrair dados de {ticker}: {e}")
            
    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        parquet_file = os.path.join(RAW_PATH, 'cotacoes_historicas.parquet')
        
        # Salva na camada Raw (.parquet) 
        # (Em produção particionaríamos por mês, mas pro MVP um arquivo resolve bem)
        logging.info(f"Salvando dados Raw em {parquet_file}...")
        df_final.to_parquet(parquet_file, engine='pyarrow', index=False)
        
        # Carga idempotente na camada Trusted (DuckDB) via UPSERT
        logging.info(f"Conectando ao DuckDB em {DB_PATH} para aplicar UPSERT...")
        conn = duckdb.connect(DB_PATH)
        
        try:
            # O DuckDB possui interoperabilidade mágica com o Pandas. Ele reconhece a variável 'df_final' no ambiente local.
            conn.execute("""
                INSERT INTO facto_cotacoes (data_pregao, id_ativo, preco_fechamento)
                SELECT data_pregao, id_ativo, preco_fechamento FROM df_final
                ON CONFLICT (data_pregao, id_ativo) DO UPDATE 
                SET preco_fechamento = EXCLUDED.preco_fechamento;
            """)
            logging.info("Carga na facto_cotacoes concluída com sucesso no DuckDB.")
        except Exception as e:
            logging.error(f"Erro durante o UPSERT no banco de dados: {e}")
            raise e
        finally:
            conn.close()
    else:
        logging.warning("Nenhum dado válido foi baixado nesta execução.")

if __name__ == "__main__":
    fetch_and_load_cotacoes()
