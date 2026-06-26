# 📐 Modelo de Dados (Data Model - DuckDB) - REVISÃO VALUE INVESTING

## Tabelas Dimensionais

### `dim_ativos`
* `id_ativo`: VARCHAR (PK) - Ex: 'BBAS3'
* `tipo_ativo`: VARCHAR - Ex: 'ACAO', 'FII'
* `setor`: VARCHAR
* [cite_start]`classificacao_lynch`: VARCHAR - Ex: 'Stalwart', 'Turnaround' [cite: 432, 500]
* [cite_start]`vantagem_competitiva_moat`: VARCHAR - Critério de Buffett [cite: 430]

### `dim_relatorios_ativos`
* `id_relatorio`: INTEGER (PK)
* `id_ativo`: VARCHAR (FK)
* `periodo_referencia`: VARCHAR
* `caminho_local_pdf`: VARCHAR - Endereço físico no volume do Docker

## Tabelas de Factos (Fact Tables)

### `facto_cotacoes`
* `data_pregao`: DATE (PK)
* `id_ativo`: VARCHAR (PK, FK)
* `preco_fechamento`: NUMERIC(10,2)

### `facto_fundamentos` (NOVO - Motor Quantitativo)
* `data_referencia`: DATE (PK)
* `id_ativo`: VARCHAR (PK, FK)
* `lpa`: NUMERIC(10,2) - Lucro por Ação
* `vpa`: NUMERIC(10,2) - Valor Patrimonial por Ação
* [cite_start]`p_l`: NUMERIC(10,2) - Múltiplo Preço/Lucro [cite: 556, 557]
* [cite_start]`roe`: NUMERIC(10,2) - Retorno sobre o Património [cite: 481]
* [cite_start]`dividend_yield`: NUMERIC(10,2) [cite: 482]
* [cite_start]`preco_justo_graham`: NUMERIC(10,2) - Calculado via sqrt(22.5 * LPA * VPA) [cite: 550]
* [cite_start]`preco_teto_bazin`: NUMERIC(10,2) - Calculado via Dividendo / 0.06 [cite: 553]
* [cite_start]`margem_seguranca_perc`: NUMERIC(10,2) - Distância entre o Preço Atual e o Preço Justo [cite: 493, 550]