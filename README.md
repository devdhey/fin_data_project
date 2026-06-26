# 📈 FinData - Pipeline de Engenharia de Dados Financeiros

Documentação Oficial e Atualizada do Projeto FinData MVP.

---

# Visão Geral

* **Objetivo do projeto:** Estruturar um pipeline automatizado de Engenharia de Dados para extração, processamento analítico e exibição de indicadores financeiros e relatórios de mercado.
* **Problema que resolve:** A dificuldade de consolidar dados históricos, calcular métricas de *valuation* em larga escala diariamente e ter um repositório centralizado de PDFs corporativos sem depender de plataformas pagas e fragmentadas.
* **Público alvo:** Investidores fundamentalistas, engenheiros de dados financeiros e analistas quantitativos.
* **Estratégia de investimento utilizada:** *Value Investing*, com a aplicação matemática dos conceitos de Benjamin Graham (Preço Justo e Margem de Segurança) e Décio Bazin (Preço Teto baseado em Dividendos).

---

# Arquitetura da Solução

O projeto é executado de forma orquestrada em contêineres e desenhado para atuar em modelo de processamento em lote (Batch).

* **Airflow:** Responsável pela orquestração. Gerencia DAGs diárias e semanais, disparando scripts de coleta, transformação e auditoria, e monitorando falhas.
* **DuckDB:** O Data Warehouse do projeto. Um banco de dados analítico (OLAP) leve, processado em memória e armazenado em arquivo físico único, ideal para alta performance em consultas.
* **Superset:** Camada de BI/Dashboard. Consome diretamente o DuckDB para apresentar os gráficos e expor os links para os PDFs arquivados.
* **Camada Raw:** Local temporário de pouso para dados não estruturados ou transacionais (como extrações em `.parquet` do YFinance).
* **Camada Analítica:** Representada pelas tabelas finais de *Factos* e *Dimensões* modeladas dentro do DuckDB.
* **Fluxo de dados:**

```text
Fontes Externas (YFinance / CVM / B3)
       │
       ▼
Scripts Python (Airflow Extractors)
       │
       ▼
Camada Raw (.parquet) / Volumes de Relatórios (PDFs)
       │
       ▼
Carga Idempotente (DuckDB)
       │
       ▼
Motor Quantitativo & Qualidade de Dados (Transformers Python)
       │
       ▼
Data Warehouse DuckDB (Tabelas Facto e Dimensão)
       │
       ▼
Apache Superset (Dashboard & Visualização)
```

---

# Escopo Atual de Ativos

## Ações
Atualmente são monitoradas 10 ações:
`BBAS3`, `EGIE3`, `CXSE3`, `ITUB4`, `VALE3`, `PETR4`, `WEGE3`, `TAEE11`, `BBDC4`, `VIVT3`.
**Por que existem:** Compõem a carteira base para o cálculo matemático das teses de Graham e Bazin e análises de múltiplos.

## Fundos Imobiliários
Atualmente monitorados:
`GARE11`, `HSLG11`.
**Por que existem:** Incluídos principalmente para a estratégia de *scraping* de Relatórios Gerenciais em PDF via portal Fundos.net (B3), mantendo o histórico físico guardado pelo projeto.

---

# Componentes Implementados

## Coleta de Cotações
* **Arquivo responsável:** `scripts/extractors/yf_extractor.py`
* **Fonte utilizada:** Yahoo Finance API (`yfinance`)
* **Frequência de atualização:** Diária (após o fechamento do mercado).

## Coleta de Balanços CVM
* **Arquivo responsável:** `scripts/extractors/cvm_scraper.py`
* **Estratégia utilizada:** Raspagem (Web Scraping) agendada semanalmente no portal RAD da CVM para obter as Demonstrações Financeiras (DFP/ITR).

## Coleta de Relatórios FII
* **Arquivo responsável:** `scripts/extractors/b3_fii_scraper.py`
* **Estratégia utilizada:** *Web Scraping* dos portais da B3/Fundos.net para realizar o download direto do PDF do Relatório Gerencial e vinculá-lo ao banco de dados.

## Motor Quantitativo
* **Arquivo responsável:** `scripts/transformers/quant_engine.py`
* **Indicadores calculados:** Lucro por Ação (LPA), Valor Patrimonial por Ação (VPA), P/L, ROE, Dividend Yield.
* **Modelos utilizados:** 
  - *Preço Justo (Benjamin Graham):* `sqrt(22.5 * LPA * VPA)`
  - *Preço Teto (Décio Bazin):* `Dividendos / 0.06`
  - *Margem de Segurança:* Percentual de desconto entre o Preço Atual e o Preço Justo.

## Data Quality
* **Arquivo responsável:** `scripts/transformers/data_quality.py`
* **Validações implementadas:** 
  1. Impedir preços fechados iguais ou menores que zero (corrompem cálculos).
  2. Impedir duplicatas lógicas de ativos no mesmo dia de pregão (falha de idempotência).
  3. Emitir alertas (Warn) para empresas que retornam VPA/LPA iguais a zero na API (podem ser empresas falidas ou inconsistências do provedor).

## Dashboard
O Apache Superset atua como a interface final.
* **Indicadores disponíveis:** Visualização dos dados agregados no DuckDB (cotações de 5 anos, margem de segurança de Graham e Bazin, e links diretos para visualizar os PDFs estruturados da CVM/B3).

---

# Estrutura do Projeto

```text
fin_data_project/
├── .vscode/               # Configurações do editor (ex: Linter Python)
├── dags/                  # Declarações das DAGs de orquestração do Airflow
│   ├── dag_auditoria_dados.py
│   ├── dag_balanços_acoes.py
│   ├── dag_cotacoes_diarias.py
│   └── dag_relatorios_fiis.py
├── docker/                # Configurações e infraestrutura Docker base
├── docs/                  # Documentação e histórico arquitetural
├── scripts/               # Scripts core do pipeline Python
│   ├── extractors/        # Scripts de coleta (Yfinance, CVM, B3)
│   ├── loaders/           # Scripts de carga (DDL e Upserts no DuckDB)
│   └── transformers/      # Motores quantitativos e regras de Data Quality
└── volumes/               # Volumes compartilhados entre containers Docker
    ├── data/              # Arquivos Raw e banco DuckDB principal
    └── reports/           # Armazenamento físico de arquivos PDF
```

* **dags/:** Contém as instruções de fluxo e horários que o Apache Airflow vai ler e executar.
* **scripts/:** Coração do projeto. Separado logicamente entre *Extract*, *Load* e *Transform*.
* **volumes/:** A garantia de que tanto o Airflow (que escreve os dados) quanto o Superset (que os lê) acessem as mesmas pastas físicas do sistema host.

---

# Fluxo de Execução

As DAGs do Airflow garantem a ordem cronológica e a dependência dos dados. O fluxo lógico correto de execução é:

1. **`fin_data_cotacoes_diarias`:** Baixa o preço atual dos ativos e inicializa o DB. Na mesma DAG (na Task final), o `quant_engine.py` é disparado para atualizar o Valuation de acordo com o preço daquele dia.
2. **`fin_data_balancos_acoes_cvm`:** Independente das cotações, raspa e busca balanços trimestrais na CVM (execução semanal).
3. **`fin_data_relatorios_fiis_b3`:** Independente das cotações, raspa novos PDFs da B3 para FIIs.
4. **`fin_data_auditoria` (Data Quality):** Roda para garantir que as tabelas modificadas pelas tarefas 1, 2 e 3 não corromperam a estrutura OLAP.

*O Motor Quantitativo depende intrinsicamente do sucesso da Coleta de Cotações, e por isso está encadeado na mesma DAG (`task_extract_load >> task_quant_engine`).*

---

# Processo de Atualização dos Dados

* **Entrada:** Via scripts Python realizando *requests* às APIs externas (Yahoo Finance) e Web Scrapers (B3, CVM).
* **Armazenamento Intermediário:** Os dados brutos batem na pasta `volumes/data` como arquivos `.parquet` temporários, enquanto os PDFs vão para `volumes/reports`.
* **Carga no DuckDB:** Os scripts da pasta `loaders` leem o `.parquet` e aplicam um `UPSERT` via SQL no arquivo `fin_database.duckdb`. Isso garante a idempotência (podemos rodar o script várias vezes sem duplicar linhas).
* **Chegada ao Superset:** O contêiner do Superset tem o volume da pasta `volumes/data` montado nele, conectando-se ao arquivo DuckDB como sua fonte de dados via driver nativo, alimentando os dashboards instantaneamente.

---

# Decisões Arquiteturais

* **Por que DuckDB?** Porque ele entrega velocidade analítica colunar sem a necessidade de manter um serviço de banco de dados (como Postgres) gastando RAM continuamente. Ele é lido como um arquivo compartilhado de alta eficiência.
* **Por que não utilizar Kafka?** Não há necessidade de mensageria em tempo real ou streaming para ações diárias ou relatórios mensais. Introduzir Kafka seria "Overengineering" inútil.
* **Por que Airflow?** Por possuir escalabilidade, gerenciamento de dependências entre tarefas e uma ótima UI para tratamento de erros em um fluxo baseado no tempo.
* **Por que processamento Batch?** Porque os mercados financeiros globais trabalham majoritariamente baseados em janelas de pregão. Obter o dado D-1 consolidado no fim do dia é o suficiente para as teses fundamentalistas adotadas.
* **Por que o valuation é aplicado apenas às ações?** FIIs não costumam reter lucro ou apresentar as mesmas métricas estruturais (VPA e LPA) que companhias de capital aberto tradicionais. O modelo de Bazin até serve para fundos, mas o projeto foca a matemática de Graham ativamente sobre as *Ações*.

---

# Escalabilidade

* **Quantidade atual de ativos:** 12 (10 Ações e 2 FIIs).
* **Limites conhecidos:** A raspagem agressiva (sem intervalos) de centenas de PDFs do sistema RAD da CVM ou da B3 pode bloquear IPs (rate limiting). O processamento no DuckDB facilmente aguenta milhões de linhas.
* **Estratégias futuras de expansão:** Inserção de *proxies* nos scrapers, divisão dos lotes de raspagem no Airflow, e migração para armazenamento S3/MinIO caso os volumes ultrapassem a capacidade local segura.
* **Possíveis otimizações:** Adicionar testes granulares Pydantic na entrada dos extratores antes que eles toquem o DuckDB.

---

# Como Executar o Projeto

1. Certifique-se de ter o Docker e Docker Compose instalados.
2. Na raiz do Superset, suba a base analítica e o orquestrador:
   ```bash
   docker-compose up -d
   ```
   *(Nota: A infraestrutura exige a subida conjunta do banco DuckDB, do Superset via seu repositório/compose local, e do Airflow configurados na rede em comum).*
3. Acesse o **Apache Airflow** no navegador (porta padrão do seu setup) para ativar as DAGs (`fin_data_cotacoes_diarias`).
4. Acesse o **Apache Superset** para configurar e visualizar o dashboard de acompanhamento, garantindo a conexão configurada apontando para `/app/fin_data/fin_database.duckdb`.

---

# Processo de Homologação

O que já foi validado e testado com sucesso durante o desenvolvimento:
* Extração contínua e sem quebra (5 anos de dados) do `yfinance`.
* Cálculos complexos usando `math.sqrt` validados para o `preco_justo_graham`.
* UPSERT no DuckDB suportando re-execuções limpas (idempotência).
* Caminho Python do repositório corrigido, permitindo as execuções modulares tanto locais quanto no Docker através da pasta `/opt/airflow/scripts`.
* Criação física dos arquivos PDF raspados no volume compartilhado (`volumes/reports`).
* Rotinas de interrupção (Crash fail-fast) do pipeline de Data Quality na presença de anomalias (Preço 0).

---

# Roadmap Futuro

* Criar um sistema de Webhooks no Airflow para alertas no Telegram ou Slack, disparados pelo pipeline de Qualidade de Dados.
* Refatorar scrapers CVM e B3 para utilizar requisições assíncronas (`aiohttp`) ou Selenium, prevenindo contra mudanças pesadas nas estruturas de DOM das corretoras.
* Incorporar lógica de conversão de Split/Grupamento nativa na base para evitar picos artificiais no Dividend Yield.

---

# Histórico de Implementação

**Fase 1 — Fundação**
* **Objetivo:** Estabelecer contêineres, orquestração e banco primário.
* **Entregas:** Volumes compartilhados, inicialização DDL do DuckDB, Script YFinance.
* **Arquivos:** `db_init.py`, `yf_extractor.py`, `dag_cotacoes_diarias.py`.
* **Resultado:** Base analítica com 5 anos de cotações perfeitamente populada sem duplicidades.

**Fase 2 — Automação de Coleta**
* **Objetivo:** Trazer relatórios não estruturados.
* **Entregas:** Scrapers em Python que varrem a CVM e B3 e fazem o download limpo.
* **Arquivos:** `cvm_scraper.py`, `b3_fii_scraper.py`, `dag_balanços_acoes.py`.
* **Resultado:** PDFs baixados diretamente no sistema de arquivos do Docker.

**Fase 3 — Motor Quantitativo**
* **Objetivo:** Gerar as métricas de inteligência da carteira.
* **Entregas:** Script que cruza preço com balanço para achar oportunidade.
* **Arquivos:** `quant_engine.py`, Atualização do `dag_cotacoes_diarias.py`.
* **Resultado:** Métricas de Bazin, Graham, Margem de Segurança e LPA/VPA/ROE sendo ingeridas por ativo.

**Fase 4 — Qualidade e Analytics**
* **Objetivo:** Blindar os dados de anomalias da internet.
* **Entregas:** Camada de Data Quality validando chaves primárias e consistência estrita.
* **Arquivos:** `data_quality.py`, `dag_auditoria_dados.py`.
* **Resultado:** Pipeline rígido com crash alert no Airflow caso o motor matemático do projeto falhe ou gere cotação espúria.