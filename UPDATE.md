# Histórico de Atualizações - Projeto FinData

Este documento reflete o estado real do projeto e as implementações finalizadas.

## O Que Foi Implementado

### 1. Motor Quantitativo Avançado (Value Investing)
- Criado o script `scripts/transformers/quant_engine.py`.
- Incorpora as teses de Benjamin Graham e Décio Bazin.
- Extrai dinamicamente dados do Yahoo Finance e calcula `LPA`, `VPA`, `P/L`, `ROE` e `Dividend Yield`.
- Gera automaticamente o `Preço Justo de Graham`, `Preço Teto de Bazin` e a `Margem de Segurança`.
- Aplicado diretamente a 10 ações do escopo principal (`BBAS3`, `EGIE3`, `CXSE3`, `ITUB4`, `VALE3`, `PETR4`, `WEGE3`, `TAEE11`, `BBDC4`, `VIVT3`).

### 2. Infraestrutura de Qualidade de Dados (Data Quality)
- Criado o script `scripts/transformers/data_quality.py`.
- Introduzido pipeline rígido de qualidade para evitar corrupção analítica no DuckDB.
- Três restrições principais validadas:
  1. Integridade de Preços (Alerta crítico para cotações zeradas ou negativas).
  2. Idempotência e Chaves Únicas (Garante que a lógica de Upsert não duplicou ativos no mesmo dia).
  3. Consistência de Fundamentos (Alerta quando API retorna `VPA` ou `LPA` zerados).

### 3. Orquestração e DAGs (Airflow)
- A orquestração via Airflow foi estendida e refatorada.
- O pipeline diário (`dag_cotacoes_diarias.py`) agora executa o motor quantitativo automaticamente após a carga do YFinance.
- Criada DAG dedicada (`dag_auditoria_dados.py`) para executar as regras do Data Quality de forma independente.
- Integrado o suporte completo no Airflow para rodar `dag_balanços_acoes.py` (CVM) e `dag_relatorios_fiis.py` (B3).

### 4. Integração DuckDB e Superset via Volumes Compartilhados
- DuckDB persistido em `volumes/data/fin_database.duckdb`.
- O Superset foi configurado para ler diretamente este banco e os relatórios (PDFs) no volume `volumes/reports`.
- Atualizado o mapeamento de volumes no Docker do Superset para integrar com o repositório (`C:/.../fin_data_project/volumes/data:/app/fin_data`).

## Situação Atual do Repositório
Todos os extratores base (YFinance, B3, CVM) estão operacionais. O banco DuckDB recebe as cotações e os cálculos do motor quantitativo diariamente. O Airflow orquestra as dependências corretamente e o Superset consome a base pronta. O foco de desenvolvimento agora transiciona para visualização avançada de dados no Dashboard e possíveis expansões do escopo de ativos.
