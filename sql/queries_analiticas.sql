-- QUERY 1: Análise de desvios críticos e prazos estourados por transportadora
SELECT
    transportador,
    COUNT(pedido_id) AS total_pedidos,
    ROUND(AVG(lead_time_real - lead_time_estimado), 2) AS media_atraso_dias,
    MAX(lead_time_real - lead_time_estimado) AS atraso_maximo,
    COUNT(CASE WHEN lead_time_real - lead_time_estimado > 5 THEN 1 END) AS ocorrencias_criticas
FROM fact_pedidos_transporte
GROUP BY transportador
ORDER BY media_atraso_dias DESC;

-- QUERY 2: Top 10 SKUs com maior perda financeira física (Shrinkage)
SELECT
    p.categoria,
    p.sku_id,
    p.custo_unitario,
    SUM(i.qtd_sistema - i.qtd_fisica) AS total_itens_perdidos,
    ROUND(SUM(i.qtd_sistema - i.qtd_fisica) * p.custo_unitario, 2) AS prejuizo_financeiro_acumulado
FROM fact_inventario_auditoria i
JOIN dim_produtos p ON i.sku_id = p.sku_id
WHERE i.qtd_sistema > i.qtd_fisica
GROUP BY p.categoria, p.sku_id, p.custo_unitario
ORDER BY prejuizo_financeiro_acumulado DESC
LIMIT 10;
