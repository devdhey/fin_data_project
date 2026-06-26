import duckdb
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = '/app/data/fin_database.duckdb'

ATIVOS_DATA = [
    ('BBAS3', 'ACAO', 'Financeiro / Bancos', 'Stalwart', 'Forte (Custos de Transição)'),
    ('EGIE3', 'ACAO', 'Utilidade Pública / Energia Elétrica', 'Stalwart', 'Forte (Ativos Regulados)'),
    ('CXSE3', 'ACAO', 'Financeiro / Seguradoras', 'Stalwart', 'Forte (Canal Exclusivo)'),
    ('ITUB4', 'ACAO', 'Financeiro / Bancos', 'Stalwart', 'Forte (Efeito de Rede)'),
    ('VALE3', 'ACAO', 'Materiais Básicos / Mineração', 'Stalwart', 'Médio (Custos de Produção)'),
    ('PETR4', 'ACAO', 'Petróleo, Gás e Biocombustíveis', 'Stalwart', 'Médio (Monopólio Técnico)'),
    ('WEGE3', 'ACAO', 'Bens Industriais / Máquinas', 'Fast Grower', 'Forte (Cultura e Eficiência)'),
    ('TAEE11', 'ACAO', 'Utilidade Pública / Energia Elétrica', 'Stalwart', 'Forte (Contratos de Longo Prazo)'),
    ('BBDC4', 'ACAO', 'Financeiro / Bancos', 'Stalwart', 'Forte (Efeito de Rede)'),
    ('VIVT3', 'ACAO', 'Telecomunicações', 'Stalwart', 'Médio (Infraestrutura)'),
    ('GARE11', 'FII', 'Logística e Industrial', 'Dividend Play', 'N/A'),
    ('HSLG11', 'FII', 'Logística', 'Dividend Play', 'N/A'),
    ('HGLG11', 'FII', 'Logística', 'Dividend Play', 'N/A'),
    ('KNCR11', 'FII', 'Títulos e Valores Mobiliários (Recebíveis)', 'Dividend Play', 'N/A'),
    ('MXRF11', 'FII', 'Híbrido (Recebíveis/Tijolo)', 'Dividend Play', 'N/A')
]

def seed_ativos():
    logging.info(f"Conectando ao DuckDB em {DB_PATH} para popular dim_ativos...")
    conn = duckdb.connect(DB_PATH)
    try:
        # Limpa e reinsere para garantir idempotência
        logging.info("Limpando dados antigos da dim_ativos...")
        conn.execute("DELETE FROM dim_ativos;")
        
        logging.info(f"Inserindo {len(ATIVOS_DATA)} ativos...")
        conn.executemany("""
            INSERT INTO dim_ativos (id_ativo, tipo_ativo, setor, classificacao_lynch, vantagem_competitiva_moat)
            VALUES (?, ?, ?, ?, ?);
        """, ATIVOS_DATA)
        
        logging.info("Verificando inserção...")
        count = conn.execute("SELECT COUNT(*) FROM dim_ativos;").fetchone()[0]
        logging.info(f"Sucesso: {count} registros inseridos em dim_ativos.")
        
    except Exception as e:
        logging.error(f"Erro ao semear a tabela dim_ativos: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed_ativos()
