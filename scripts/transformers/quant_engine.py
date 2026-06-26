import yfinance as yf
import pandas as pd
import duckdb
import logging
import math
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = '/app/data/fin_database.duckdb'

# Ações do escopo real da carteira.
ACOES_MVP = [
    'BBAS3.SA', 'EGIE3.SA', 'CXSE3.SA', 'ITUB4.SA', 'VALE3.SA', 
    'PETR4.SA', 'WEGE3.SA', 'TAEE11.SA', 'BBDC4.SA', 'VIVT3.SA'
]

def calc_graham(lpa, vpa):
    """
    Calcula o Preço Justo segundo Benjamin Graham: sqrt(22.5 * LPA * VPA)
    """
    if lpa is not None and vpa is not None and lpa > 0 and vpa > 0:
        return math.sqrt(22.5 * lpa * vpa)
    return 0.0

def calc_bazin(dividend_rate):
    """
    Calcula o Preço Teto segundo Décio Bazin: Dividendo Pago / 0.06
    """
    if dividend_rate is not None and dividend_rate > 0:
        return dividend_rate / 0.06
    return 0.0

def generate_fundamentos():
    """
    Motor quantitativo: extrai fundamentos-base, roda a matemática financeira
    das teses de investimento (Value Investing) e alimenta o Data Warehouse.
    """
    conn = duckdb.connect(DB_PATH)
    data_ref = datetime.today().date()
    
    records = []
    
    try:
        for ticker in ACOES_MVP:
            logging.info(f"Processando Motor Quantitativo para: {ticker}")
            ativo_obj = yf.Ticker(ticker)
            info = ativo_obj.info
            
            # Coleta de Fatos Isolados
            lpa = info.get('trailingEps', 0)
            vpa = info.get('bookValue', 0)
            p_l = info.get('trailingPE', 0)
            roe = info.get('returnOnEquity', 0)
            
            # Formatações (% -> Real)
            roe_perc = roe * 100 if roe else 0.0
            
            div_yield = info.get('dividendYield', 0)
            div_yield_perc = div_yield * 100 if div_yield else 0.0
            
            dividend_rate = info.get('trailingAnnualDividendRate', 0)
            preco_atual = info.get('currentPrice', info.get('previousClose', 0))
            
            # Motor de Cálculos (Valuation)
            preco_graham = calc_graham(lpa, vpa)
            preco_bazin = calc_bazin(dividend_rate)
            
            # Margem de segurança frente ao Graham
            margem_seg = 0.0
            if preco_atual and preco_atual > 0 and preco_graham > 0:
                margem_seg = ((preco_graham - preco_atual) / preco_graham) * 100
            
            id_ativo = ticker.replace('.SA', '')
            
            records.append({
                'data_referencia': data_ref,
                'id_ativo': id_ativo,
                'lpa': round(lpa, 2) if lpa else 0,
                'vpa': round(vpa, 2) if vpa else 0,
                'p_l': round(p_l, 2) if p_l else 0,
                'roe': round(roe_perc, 2),
                'dividend_yield': round(div_yield_perc, 2),
                'preco_justo_graham': round(preco_graham, 2),
                'preco_teto_bazin': round(preco_bazin, 2),
                'margem_seguranca_perc': round(margem_seg, 2)
            })
            logging.info(f"Métricas (Graham, Bazin, ROE) de {ticker} calculadas com sucesso.")

        if records:
            df_fundamentos = pd.DataFrame(records)
            
            logging.info("Realizando carga idempotente (UPSERT) na tabela facto_fundamentos...")
            conn.execute("""
                INSERT INTO facto_fundamentos (
                    data_referencia, id_ativo, lpa, vpa, p_l, roe, 
                    dividend_yield, preco_justo_graham, preco_teto_bazin, margem_seguranca_perc
                )
                SELECT * FROM df_fundamentos
                ON CONFLICT (data_referencia, id_ativo) DO UPDATE SET 
                    lpa = EXCLUDED.lpa,
                    vpa = EXCLUDED.vpa,
                    p_l = EXCLUDED.p_l,
                    roe = EXCLUDED.roe,
                    dividend_yield = EXCLUDED.dividend_yield,
                    preco_justo_graham = EXCLUDED.preco_justo_graham,
                    preco_teto_bazin = EXCLUDED.preco_teto_bazin,
                    margem_seguranca_perc = EXCLUDED.margem_seguranca_perc;
            """)
            logging.info("Motor Quantitativo processou e salvou os dados analíticos com sucesso.")
            
    except Exception as e:
        logging.error(f"Erro no Motor Quantitativo: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    generate_fundamentos()
