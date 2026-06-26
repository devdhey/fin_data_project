# 📋 Backlog Técnico de Desenvolvimento do Projeto

Este documento detalha o planejamento técnico das tarefas de engenharia de dados do projeto FinData, mapeando prioridades, complexidades (estimadas em Story Points - SP), dependências, benefícios práticos de cada entrega e arquivos afetados.

---

## 🟩 Fase 1 - Fundação

### 1. Configuração da Infraestrutura Docker e Ambiente
* **Prioridade:** Alta
* **Complexidade:** Média (3 SP)
* **Dependências:** Nenhuma
* **Benefício para o projeto:** Garante a portabilidade e a paridade de ambiente (desenvolvimento/produção) executando o Apache Airflow e o Apache Superset sob uma mesma rede Docker (`fin_network`) com volumes compartilhados.
* **Arquivos envolvidos:**
  * [docker-compose.yml](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/docker/docker-compose.yml) [NEW]
  * [airflow.Dockerfile](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/docker/airflow.Dockerfile) [NEW]
  * [requirements.txt](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/docker/requirements.txt) [NEW]

### 2. Modelagem de Dados e Inicialização do DuckDB
* **Prioridade:** Alta
* **Complexidade:** Média (3 SP)
* **Dependências:** Configuração da Infraestrutura Docker e Ambiente
* **Benefício para o projeto:** Criação física do banco de dados relacional colunar ACID (`fin_database.duckdb`) no volume persistente e definição dos esquemas das tabelas dimensionais (`dim_ativos`, `dim_relatorios_ativos`) e de fatos (`facto_cotacoes`).
* **Arquivos envolvidos:**
  * [db_initializer.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/loaders/db_initializer.py) [NEW]
  * [04_DATA_MODEL.md](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/docs/04_DATA_MODEL.md) [MODIFY]
  * [fin_database.duckdb](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/volumes/data/fin_database.duckdb) [NEW/IGNORE]

### 3. Módulo de Extração de Cotações Históricas (`yf_extractor.py`)
* **Prioridade:** Alta
* **Complexidade:** Média (3 SP)
* **Dependências:** Inicialização do DuckDB
* **Benefício para o projeto:** Conexão robusta à API do `yfinance` para extrair cotações diárias e o histórico de 5 anos dos ativos iniciais da carteira MVP (BBAS3, EGIE3, CXSE3, GARE11, HSLG11).
* **Arquivos envolvidos:**
  * [yf_extractor.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/extractors/yf_extractor.py) [NEW]

### 4. Módulo de Carga Idempotente no DuckDB (`db_loader.py`)
* **Prioridade:** Alta
* **Complexidade:** Alta (5 SP)
* **Dependências:** Módulo de Extração de Cotações Históricas
* **Benefício para o projeto:** Implementa rotinas de carga de dados com estratégia de escrita idempotente (UPSERT/Merge), evitando registros duplicados em caso de falhas e reprocessamento das DAGs.
* **Arquivos envolvidos:**
  * [db_loader.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/loaders/db_loader.py) [NEW]

### 5. DAG de Ingestão de Cotações Diárias no Airflow (`dag_cotacoes_diarias.py`)
* **Prioridade:** Alta
* **Complexidade:** Média (3 SP)
* **Dependências:** Módulo de Carga Idempotente
* **Benefício para o projeto:** Automatização do agendamento diário de ingestão de dados de mercado (pós-fechamento do pregão), executando o extrator e o loader de maneira orquestrada dentro do container Airflow.
* **Arquivos envolvidos:**
  * [dag_cotacoes_diarias.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/dags/dag_cotacoes_diarias.py) [NEW]

---

## 🟨 Fase 2 - Captura de Documentos

### 1. Web Scraper de Balanços Trimestrais (CVM/Ações)
* **Prioridade:** Alta
* **Complexidade:** Alta (5 SP)
* **Dependências:** Modelagem de Dados e Inicialização do DuckDB
* **Benefício para o projeto:** Captura automática das Demonstrações Financeiras Padronizadas (DFP) e Informações Trimestrais (ITR) do portal da CVM, estruturando os balanços corporativos de BBAS3, EGIE3 e CXSE3.
* **Arquivos envolvidos:**
  * [cvm_scraper.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/extractors/cvm_scraper.py) [NEW]
  * [dag_balancos_acoes.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/dags/dag_balancos_acoes.py) [NEW]

### 2. Web Scraper de Relatórios Gerenciais (B3/Fundos.net/FIIs)
* **Prioridade:** Alta
* **Complexidade:** Alta (8 SP)
* **Dependências:** Modelagem de Dados e Inicialização do DuckDB
* **Benefício para o projeto:** Download e armazenamento automatizado dos PDFs de relatórios gerenciais mensais de FIIs (GARE11, HSLG11) a partir do portal Fundos.net para o volume físico compartilhado.
* **Arquivos envolvidos:**
  * [b3_pdf_scraper.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/extractors/b3_pdf_scraper.py) [NEW]
  * [dag_relatorios_fiis.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/dags/dag_relatorios_fiis.py) [NEW]

### 3. Integração de Links Dinâmicos de PDFs no Apache Superset
* **Prioridade:** Média
* **Complexidade:** Média (3 SP)
* **Dependências:** Scrapers de Balanços e Relatórios Gerenciais
* **Benefício para o projeto:** Permite que o usuário acesse e leia os relatórios gerenciais em PDF diretamente a partir do dashboard de Superset através de caminhos/URLs locais mapeados.
* **Arquivos envolvidos:**
  * [01_ARCHITECTURE.md](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/docs/01_ARCHITECTURE.md) [MODIFY]

---

## 🟦 Fase 3 - Motor quantitativo e analytics

### 1. Cálculo de Indicadores e Fórmulas de Valuation (`facto_fundamentos`)
* **Prioridade:** Alta
* **Complexidade:** Alta (8 SP)
* **Dependências:** Carga de cotações (Fase 1) e extração CVM/B3 (Fase 2)
* **Benefício para o projeto:** Processamento e cálculo no banco analítico de múltiplos de Value Investing históricos e atualizados (LPA, VPA, ROE, P/L, DY) e métricas quantitativas de valuation: Preço Justo de Graham, Preço Teto de Bazin e Margem de Segurança.
* **Arquivos envolvidos:**
  * [indicators_calculator.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/transformers/indicators_calculator.py) [NEW]
  * [04_DATA_MODEL.md](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/docs/04_DATA_MODEL.md) [MODIFY]

### 2. Modelagem de Views Analíticas para Superset
* **Prioridade:** Média
* **Complexidade:** Média (3 SP)
* **Dependências:** Cálculo de Indicadores e Fórmulas de Valuation
* **Benefício para o projeto:** Geração de consultas e views consolidadas (denormalizadas e limpas) no DuckDB, otimizando drasticamente o desempenho e a simplicidade de construção dos gráficos no Apache Superset.
* **Arquivos envolvidos:**
  * [create_views.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/loaders/create_views.py) [NEW]

### 3. Escalonamento da Carteira (Ingestão dos 16 ativos restantes)
* **Prioridade:** Média
* **Complexidade:** Baixa (2 SP)
* **Dependências:** Pipelines da Fase 1 e 2 homologados com ativos MVP
* **Benefício para o projeto:** Amplia o escopo do Data Warehouse de 5 ativos (MVP) para os 21 ativos da carteira total, consolidando a ingestão definitiva.
* **Arquivos envolvidos:**
  * [yf_extractor.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/scripts/extractors/yf_extractor.py) [MODIFY]

---

## 🟪 Fase 4 - testes

### 1. Testes Unitários de Extratores e Scrapers
* **Prioridade:** Média
* **Complexidade:** Média (3 SP)
* **Dependências:** Módulos de Ingestão criados (Fase 1 e 2)
* **Benefício para o projeto:** Valida se as conexões de API (`yfinance`) e as rotinas de HTML scraping (B3/CVM) funcionam perfeitamente e avisa antecipadamente sobre eventuais quebras em layouts externos.
* **Arquivos envolvidos:**
  * [test_yf_extractor.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/tests/test_yf_extractor.py) [NEW]
  * [test_scrapers.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/tests/test_scrapers.py) [NEW]

### 2. Testes de Idempotência e Integridade de Dados no DuckDB
* **Prioridade:** Alta
* **Complexidade:** Média (3 SP)
* **Dependências:** Inicialização do DuckDB e Módulo de Carga
* **Benefício para o projeto:** Validação de restrições de chaves primárias, ausência de nulos inesperados em colunas críticas e integridade das fórmulas de valuation calculadas na base de dados.
* **Arquivos envolvidos:**
  * [test_db_integrity.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/tests/test_db_integrity.py) [NEW]

### 3. Testes de Integração e Sintaxe de DAGs no Airflow
* **Prioridade:** Média
* **Complexidade:** Baixa (2 SP)
* **Dependências:** DAGs do Airflow criadas (Fase 1 e 2)
* **Benefício para o projeto:** Garante que os arquivos de definição das DAGs (`dags/`) sejam livres de erros sintáticos Python e não possuam loops cíclicos, evitando falhas de carregamento no servidor do Airflow.
* **Arquivos envolvidos:**
  * [test_airflow_dags.py](file:///c:/Users/Dheymes%20Alves/Documents/Dheymes/Desenvolvimento/GitHub/Projetos/fin_data_project/tests/test_airflow_dags.py) [NEW]
