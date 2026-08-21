-- 1 basic information of the whole dataset: orders, customers, revenue, profit margin, and average order size. 
SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT customer_name) AS unique_customers,
    SUM(quantity) AS units_sold,
    ROUND(SUM(revenue)::numeric, 2) AS total_revenue,
    ROUND(SUM(profit)::numeric, 2) AS total_profit,
    ROUND((SUM(profit) /SUM(revenue) * 100)::numeric, 2) AS profit_margin_pct,
    ROUND((SUM(revenue) / COUNT(*))::numeric, 2) AS avg_order_value
FROM "Sales Orders"

-- 2 Same metrics but broken out by month, so we can see if there's any seasonal changes
SELECT 
	DISTINCT EXTRACT (MONTH FROM order_date) AS month,
	COUNT(*) AS orders,
    ROUND(SUM(revenue)::numeric, 2)AS revenue,
    ROUND(SUM(profit)::numeric, 2)AS profit,
    ROUND((SUM(profit) / SUM(revenue) * 100)::numeric, 2) AS margin_pct
FROM "Sales Orders"
GROUP BY month
ORDER BY month

-- 3 Which categories bring in the most revenue vs which are actually the most profitable
SELECT 
    category,
	COUNT(*) AS orders,
    ROUND(SUM(revenue)::numeric, 2)AS revenue,
    ROUND(SUM(profit)::numeric, 2)AS profit,
	ROUND((SUM(profit) / SUM(revenue) * 100)::numeric, 2) AS margin_pct,
	RANK() OVER(ORDER BY SUM(revenue) DESC) as revenue_ranking,
	RANK() OVER(ORDER BY (SUM(profit) / SUM(revenue) * 100) DESC) as margin_ranking
FROM "Sales Orders"
GROUP BY category
ORDER BY revenue desc

-- 4 Which region bring in the most revenue vs which are actually the most profitable
SELECT 
	region,
    ROUND(SUM(revenue)::numeric, 2)AS revenue,
    ROUND(SUM(profit)::numeric, 2)AS profit,
	ROUND((SUM(profit) / SUM(revenue) * 100)::numeric, 2) AS margin_pct
FROM "Sales Orders"
GROUP BY region
ORDER BY revenue DESC
