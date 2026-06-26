# 📋 Backlog de Desenvolvimento do Projeto

## 🟩 Fase 1: Infraestrutura e Carga Histórica (Atual)
- [ ] Construir infraestrutura Docker (Requirements, Dockerfile, Compose).
- [ ] [cite_start]Desenvolver Módulo `yf_extractor.py` para carga de cotações de 5 anos[cite: 105].
- [ ] Implementar a primeira DAG do Airflow (`dag_cotacoes_diarias.py`).
- [ ] Inicializar o DuckDB e testar a escrita idempotente.

## 🟨 Fase 2: Scraping de Documentos Oficiais
- [ ] [cite_start]Desenvolver Web Scraper para Balanços Trimestrais (CVM/Ações)[cite: 111, 114].
- [ ] [cite_start]Desenvolver Web Scraper para Relatórios Gerenciais (B3/FIIs)[cite: 112, 116].
- [ ] [cite_start]Implementar links dinâmicos no Apache Superset[cite: 124, 152].

## 🟦 Fase 3: Escalonamento da Carteira
- [ ] [cite_start]Mapeamento e ingestão dos 16 ativos restantes da carteira total (Mover do MVP para Produção)[cite: 36, 44].