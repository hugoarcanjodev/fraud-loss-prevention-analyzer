import sqlite3
import pandas as pd
import numpy as np
import random

def generate_mvp_database():
    # Configuração de reprodutibilidade
    np.random.seed(42)
    random.seed(42)
    
    # 1. Conectar ao SQLite (Cria o arquivo automaticamente se não existir)
    conn = sqlite3.connect('data/fraud_analytics.db')
    cursor = conn.cursor()
    
    # 2. Criar Tabelas (DDL)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dim_produtos (
        sku_id TEXT PRIMARY KEY,
        categoria TEXT,
        custo_unitario REAL,
        alto_valor_flag INTEGER
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fact_pedidos_transporte (
        pedido_id TEXT PRIMARY KEY,
        sku_id TEXT,
        transportador TEXT,
        lead_time_estimado INTEGER,
        lead_time_real INTEGER,
        FOREIGN KEY (sku_id) REFERENCES dim_produtos (sku_id)
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fact_inventario_auditoria (
        auditoria_id TEXT PRIMARY KEY,
        sku_id TEXT,
        qtd_sistema INTEGER,
        qtd_fisica INTEGER,
        data_auditoria TEXT,
        FOREIGN KEY (sku_id) REFERENCES dim_produtos (sku_id)
    );
    ''')
    
    # 3. Gerar Dimensão Produtos
    num_produtos = 50
    skus = [f'SKU_{1000+i}' for i in range(num_produtos)]
    categorias = ['Eletrônicos', 'Eletrodomésticos', 'Vestuário', 'Alimentos', 'Cosméticos']
    
    produtos_data = []
    for sku in skus:
        cat = random.choice(categorias)
        # Eletrônicos e eletrodomésticos tendem a ser mais caros na simulação
        if cat in ['Eletrônicos', 'Eletrodomésticos']:
            custo = round(random.uniform(800, 2500), 2)
        else:
            custo = round(random.uniform(15, 300), 2)
        
        alto_valor = 1 if custo > 1000 else 0
        produtos_data.append((sku, cat, custo, alto_valor))
        
    cursor.executemany('INSERT OR REPLACE INTO dim_produtos VALUES (?, ?, ?, ?);', produtos_data)
    
    # 4. Gerar Fato Transporte (Com anomalia injetada na TransLog)
    num_pedidos = 1200
    transportadores = ['TransLog', 'ExpressBR', 'RotaSegura', 'FreteRapido']
    pedidos_data = []
    
    for i in range(num_pedidos):
        pedido_id = f'PED_{50000+i}'
        sku = random.choice(skus)
        transp = random.choice(transportadores)
        lt_estimado = random.randint(2, 5)
        
        # Padrão anômalo: se for a TransLog, há 15% de chance de atraso extremo (suspeita de desvio/fraude)
        if transp == 'TransLog' and random.random() < 0.15:
            lt_real = lt_estimado + random.randint(7, 14)
        else:
            lt_real = lt_estimado + int(np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1]))
            
        pedidos_data.append((pedido_id, sku, transp, lt_estimado, lt_real))
        
    cursor.executemany('INSERT OR REPLACE INTO fact_pedidos_transporte VALUES (?, ?, ?, ?, ?);', pedidos_data)
    
    # 5. Gerar Fato Inventário (Com anomalia de quebra física/furto em Eletrônicos de alto valor)
    num_auditorias = 300
    df_prod_temp = pd.DataFrame(produtos_data, columns=['sku_id', 'categoria', 'custo_unitario', 'alto_valor_flag'])
    auditorias_data = []
    
    for i in range(num_auditorias):
        auditoria_id = f'AUD_{9000+i}'
        escolha = df_prod_temp.sample(n=1).iloc[0]
        sku = escolha['sku_id']
        cat = escolha['categoria']
        alto_valor = escolha['alto_valor_flag']
        
        qtd_sistema = random.randint(40, 300)
        
        # Padrão anômalo: se for Eletrônico de Alto Valor, há forte chance de sumiço físico (Shrinkage)
        if cat == 'Eletrônicos' and alto_valor == 1 and random.random() < 0.30:
            qtd_fisica = qtd_sistema - random.randint(4, 18)
        else:
            qtd_fisica = qtd_sistema - int(np.random.choice([0, 1], p=[0.9, 0.1]))
            
        data_aud = f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        auditorias_data.append((auditoria_id, sku, qtd_sistema, qtd_fisica, data_aud))
        
    cursor.executemany('INSERT OR REPLACE INTO fact_inventario_auditoria VALUES (?, ?, ?, ?, ?);', auditorias_data)
    
    conn.commit()
    conn.close()
    print("Banco de dados SQLite 'fraud_analytics.db' gerado com sucesso em data/ com dados simulados!")

if __name__ == '__main__':
    generate_mvp_database()
