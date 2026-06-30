import duckdb
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminhos Inteligentes (Docker vs Local)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists('/app/data'):
    DB_PATH = '/app/data/fin_database.duckdb'
else:
    DB_PATH = os.path.join(BASE_DIR, 'volumes', 'data', 'fin_database.duckdb')

def init_db():
    logging.info(f"Iniciando a conexão com o DuckDB em: {DB_PATH}")
    
    # Garantir que a pasta base exista caso seja executado fora do contexto mapeado
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = duckdb.connect(DB_PATH)
    
    try:
        # Tabela Dimension: dim_ativos
        logging.info("Criando/Validando tabela: dim_ativos...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_ativos (
                id_ativo VARCHAR PRIMARY KEY,
                tipo_ativo VARCHAR,
                setor VARCHAR,
                classificacao_lynch VARCHAR,
                vantagem_competitiva_moat VARCHAR
            );
        """)

        # Tabela Dimension: dim_relatorios_ativos
        logging.info("Criando/Validando tabela: dim_relatorios_ativos...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_relatorios_ativos (
                id_relatorio INTEGER PRIMARY KEY,
                id_ativo VARCHAR,
                periodo_referencia VARCHAR,
                caminho_local_pdf VARCHAR
            );
        """)

        # Tabela de Facto: facto_cotacoes
        logging.info("Criando/Validando tabela: facto_cotacoes...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facto_cotacoes (
                data_pregao DATE,
                id_ativo VARCHAR,
                preco_fechamento NUMERIC(10,2),
                PRIMARY KEY (data_pregao, id_ativo)
            );
        """)

        # Tabela de Facto: facto_fundamentos
        logging.info("Criando/Validando tabela: facto_fundamentos...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facto_fundamentos (
                data_referencia DATE,
                id_ativo VARCHAR,
                lpa NUMERIC(10,2),
                vpa NUMERIC(10,2),
                p_l NUMERIC(10,2),
                roe NUMERIC(10,2),
                dividend_yield NUMERIC(10,2),
                preco_justo_graham NUMERIC(10,2),
                preco_teto_bazin NUMERIC(10,2),
                margem_seguranca_perc NUMERIC(10,2),
                PRIMARY KEY (data_referencia, id_ativo)
            );
        """)
        
        logging.info("Migrações concluídas (Idempotência garantida). Todas as tabelas foram validadas.")
        
    except Exception as e:
        logging.error(f"Erro durante a criação das tabelas no DuckDB: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
