import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Fraud Loss Prevention Analyzer", layout="wide", page_icon="🕵️")

st.title("🕵️ Fraud Loss Prevention Analyzer")
st.caption("MVP: Monitoramento e Auditoria de Fraudes de Frete e Quebras Físicas (Shrinkage)")

# Conexão com o banco de dados
def run_query(query):
    try:
        conn = sqlite3.connect('data/fraud_analytics.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco. Certifique-se de rodar o gerador primeiro: {e}")
        return pd.DataFrame()

# Carregar dados principais para os KPIs principais
df_transp = run_query('''
    SELECT transportador, 
           (lead_time_real - lead_time_estimado) as atraso 
    FROM fact_pedidos_transporte;
''')

df_perdas = run_query('''
    SELECT p.categoria, p.sku_id, p.custo_unitario, p.alto_valor_flag,
           (i.qtd_sistema - i.qtd_fisica) as itens_perdidos
    FROM fact_inventario_auditoria i
    JOIN dim_produtos p ON i.sku_id = p.sku_id
    WHERE i.qtd_sistema > i.qtd_fisica;
''')

if not df_transp.empty and not df_perdas.empty:
    
    # ------------------- CAMADA DE CARDS (KPIs MESTRES) -------------------
    total_pedidos = len(df_transp)
    ocorr_criticas = len(df_transp[df_transp['atraso'] > 5])
    
    df_perdas['prejuizo'] = df_perdas['itens_perdidos'] * df_perdas['custo_unitario']
    prejuizo_total = df_perdas['prejuizo'].sum()
    itens_sumidos = df_perdas['itens_perdidos'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Pedidos Auditados", f"{total_pedidos:,}")
    col2.metric("Ocorrências Críticas (>5 dias)", f"{ocorr_criticas}", delta="Atenção à Rotas", delta_color="inverse")
    col3.metric("Prejuízo Acumulado (Shrinkage)", f"R$ {prejuizo_total:,.2f}", delta="Risco Alto", delta_color="inverse")
    col4.metric("Total de Itens Extraviados", f"{itens_sumidos} un")
    
    st.markdown("---")
    
    # ------------------- ABA 1: FRAUDES EM TRANSPORTES -------------------
    st.subheader("🚨 Inteligência de Transportes & Red Flags de Lead Time")
    
    metrics_transp = run_query('''
        SELECT transportador,
               COUNT(pedido_id) AS total_pedidos,
               ROUND(AVG(lead_time_real - lead_time_estimado), 2) AS media_atraso_dias,
               COUNT(CASE WHEN lead_time_real - lead_time_estimado > 5 THEN 1 END) AS ocorrencias_criticas
        FROM fact_pedidos_transporte
        GROUP BY transportador;
    ''')
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("**Métricas Consolidadas por Parceiro**")
        st.dataframe(metrics_transp, use_container_width=True, hide_index=True)
    with c2:
        fig_box = px.box(df_transp, x="transportador", y="atraso", 
                         title="Dispersão de Dias de Atraso por Transportadora",
                         labels={"atraso": "Dias de Atraso real vs. acordado", "transportador": "Parceiro Logístico"},
                         color="transportador", color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_box, use_container_width=True)
        
    st.markdown("---")
    
    # ------------------- ABA 2: PREVENÇÃO DE PERDAS (AUDITORIA) -------------------
    st.subheader("📦 Auditoria de Inventário Físico vs Sistêmico")
    
    df_cat = df_perdas.groupby('categoria').agg(
        total_perdido=('itens_perdidos', 'sum'),
        prejuizo_total=('prejuizo', 'sum')
    ).reset_index().sort_values(by='prejuizo_total', ascending=False)
    
    c3, c4 = st.columns(2)
    with c3:
        fig_bar = px.bar(df_cat, x="categoria", y="prejuizo_total",
                         title="Impacto Financeiro Acumulado por Categoria (R$)",
                         labels={"prejuizo_total": "Prejuízo Acumulado (R$)", "categoria": "Categoria"},
                         text_auto='.2s', color="categoria", color_discrete_sequence=px.colors.qualitative.Dark2)
        st.plotly_chart(fig_bar, use_container_width=True)
    with c4:
        st.markdown("**Top 5 SKUs Críticos (Foco de Furto/Perda Operacional)**")
        top_skus = df_perdas.groupby(['categoria', 'sku_id', 'custo_unitario']).agg(
            unidades_perdidas=('itens_perdidos', 'sum'),
            prejuizo_total=('prejuizo', 'sum')
        ).reset_index().sort_values(by='prejuizo_total', ascending=False).head(5)
        
        st.dataframe(top_skus, use_container_width=True, hide_index=True)
        st.caption("💡 Recomendação Técnica: SKUs acima devem ser movidos para gaiolas de alta segurança imediatamente.")

else:
    st.warning("Banco de dados vazio ou não encontrado. Execute o comando `python data/generator.py` para alimentar o sistema.")
