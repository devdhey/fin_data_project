# 🏛️ Documentação de Arquitetura

## Topologia dos Contêineres
* [cite_start]**Network:** `fin_network` (bridge) isola a comunicação interna[cite: 144].
* [cite_start]**Persistência Compartilhada:** * `shared_data_vol` ➔ montado em `/app/data` no Airflow Worker e no Superset[cite: 146]. Contém o arquivo ACID `fin_database.duckdb`.
  * [cite_start]`reports_vol` ➔ montado em `/app/reports`[cite: 149]. [cite_start]Armazena os PDFs brutos baixados via scraping[cite: 150].

## Camadas de Dados
1. **Raw (Arquivos):** Ingestão pura do `yfinance` e scrapers salva em partições locais no formato `.parquet` (`/app/data/raw/`).
2. **Trusted/Analytics (DuckDB):** Tabelas normalizadas, indexadas e otimizadas para leitura colunária pelo Superset.