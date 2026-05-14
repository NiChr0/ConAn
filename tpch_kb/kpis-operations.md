# KPIs — Operations

## OPS-001: agg_daily_orders_totalprice
**Tier:** L1  
**Maturity:** Validated  
**Confidence Ceiling:** 90%  
**Source Table:** fct_orders  
**Description:** Total aggregated revenue generated from all orders on a given day. This is a core measure of sales performance.  
**Formula:** SUM(fct_orders.totalprice)  
**Notes:** Promoted to L1 core metric. Assumes 'totalprice' represents the revenue amount.  
