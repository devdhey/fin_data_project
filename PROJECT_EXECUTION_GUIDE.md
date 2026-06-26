# 🧭 PROJECT_EXECUTION_GUIDE (Guia de Execução do Agente)

Este guia é de leitura **obrigatória** e compulsória para qualquer agente de IA ou CLI antes de propor, modificar ou criar qualquer código neste repositório.

## 1. Princípios de Atuação no Código
* **Idempotência Absoluta:** Scripts de ingestão e tarefas do Airflow devem ser capazes de rodar múltiplas vezes sem duplicar registros no DuckDB.
* **Isolamento de Ambiente:** Nenhum código pode assumir caminhos absolutos do host local. Todo o ecossistema deve rodar indexado aos caminhos dos volumes mapeados no Docker (`/app/data` e `/app/reports`).
* **Abordagem Defensiva:** Antes de modificar tabelas no DuckDB ou esquemas de arquivos `.parquet`, o script deve verificar se a estrutura já existe, registrando logs detalhados em caso de falha.

## 2. Protocolo de Alteração de Código (Passo a Passo)
Sempre que receber uma instrução para criar uma nova feature ou alterar o pipeline:

1. **Fase de Descoberta:** Faça um scan em `docker/docker-compose.yml` e `scripts/` para entender as dependências ativas.
2. **Checagem do Backlog:** Consulte `docs/02_BACKLOG.md` para validar se a tarefa já está mapeada ou se colide com outra entrega.
3. **Validação de Impacto Fundamental:** Verifique se a alteração afeta o cálculo das métricas de Valuation/Múltiplos ou o fluxo dos PDFs exigidos na tese de investimento.
4. **Execução Incremental:** Nunca reescreva um arquivo inteiro se puder modularizá-lo. Crie funções auxiliares isoladas.

## 3. Modo de Resposta do Agente
* Ao propor códigos, separe os blocos por caminho de arquivo (ex: `### Alteração em: dags/dag_cotacoes_diarias.py`).
* Justifique qual decisão de Engenharia de Dados (Performance, Compressão de IO ou Isolamento de Rede) motivou a escrita daquele bloco de código.