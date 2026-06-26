# pyrefly: ignore [missing-import]
import duckdb
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = '/app/data/fin_database.duckdb'

def run_data_quality_checks():
    """
    Roda um conjunto de regras de Qualidade de Dados (Data Quality Constraints)
    diretamente no banco de dados analítico. Lança uma exceção forçando a queda
    da DAG caso alguma anomalia crítica seja identificada.
    """
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    try:
        logging.info("Iniciando bateria de testes de Qualidade de Dados (DQ)...")
        
        # Teste 1: Preços Zero ou Negativos na camada Fato
        # Um preço igual a zero ou negativo destrói os cálculos de Margem de Segurança
        res_preco = conn.execute("""
            SELECT COUNT(*) FROM facto_cotacoes 
            WHERE preco_fechamento <= 0
        """).fetchone()[0]
        
        if res_preco > 0:
            raise ValueError(f"CRÍTICO (DQ): Encontrados {res_preco} registros com preço zerado ou negativo na facto_cotacoes.")
        logging.info("[PASS] Teste 1: Consistência Matemática de Cotações (Nenhum valor <= 0).")
            
        # Teste 2: Duplicidade de Chave Lógica (Idempotência quebrada)
        # Verifica se por falha do Upsert temos o mesmo ativo 2x no mesmo dia
        res_dup = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT id_ativo, data_pregao
                FROM facto_cotacoes
                GROUP BY id_ativo, data_pregao
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]
        
        if res_dup > 0:
            raise ValueError(f"CRÍTICO (DQ): Encontradas {res_dup} ocorrências de cotações duplicadas para o mesmo ativo no mesmo dia.")
        logging.info("[PASS] Teste 2: Integridade de Chaves Únicas (Nenhuma duplicata).")
            
        # Teste 3: Fundamentos Corrompidos (Alerta de API)
        # É possível uma empresa ter lucro zero e VPA zero se estiver falida, mas em nossa carteira 
        # isso provavelmente é falha momentânea da API do Yahoo Finance.
        res_fund = conn.execute("""
            SELECT COUNT(*) FROM facto_fundamentos 
            WHERE vpa = 0 OR lpa = 0
        """).fetchone()[0]
        
        if res_fund > 0:
            logging.warning(f"AVISO (DQ): {res_fund} registros em facto_fundamentos possuem LPA ou VPA = 0. Avalie instabilidade na API ou falência da empresa referida.")
        logging.info("[PASS/WARN] Teste 3: Rastreio de Múltiplos Nulos.")
        
        logging.info("=> SUCESSO: Todos os testes rigorosos de Data Quality foram aprovados no Data Warehouse.")

    except Exception as e:
        logging.error(f"FALHA NO PIPELINE DE QUALIDADE: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    run_data_quality_checks()
