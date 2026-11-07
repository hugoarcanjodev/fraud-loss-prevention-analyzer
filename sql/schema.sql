-- DDL para criação do Banco de Dados Relacional - Fraud Loss Prevention Analyzer

-- 1. Tabela Dimensional de Cadastro de Produtos
CREATE TABLE IF NOT EXISTS dim_produtos (
    sku_id TEXT PRIMARY KEY,
    categoria TEXT NOT NULL,
    custo_unitario REAL NOT NULL,
    alto_valor_flag INTEGER NOT NULL CHECK (alto_valor_flag IN (0, 1))
);

-- 2. Tabela Fato de Histórico de Transporte e Pedidos
CREATE TABLE IF NOT EXISTS fact_pedidos_transporte (
    pedido_id TEXT PRIMARY KEY,
    sku_id TEXT NOT NULL,
    transportador TEXT NOT NULL,
    lead_time_estimado INTEGER NOT NULL,
    lead_time_real INTEGER NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES dim_produtos (sku_id) ON DELETE CASCADE
);

-- 3. Tabela Fato de Auditoria Cíclica de Inventário
CREATE TABLE IF NOT EXISTS fact_inventario_auditoria (
    auditoria_id TEXT PRIMARY KEY,
    sku_id TEXT NOT NULL,
    qtd_sistema INTEGER NOT NULL CHECK (qtd_sistema >= 0),
    qtd_fisica INTEGER NOT NULL CHECK (qtd_fisica >= 0),
    data_auditoria TEXT NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES dim_produtos (sku_id) ON DELETE CASCADE
);
