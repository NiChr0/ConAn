# KPIs — Revenue

## REV-001: agg_monthly_lineitem_revenue
**Tier:** L0  
**Maturity:** Validated  
**Confidence Ceiling:** 90%  
**Source Table:** fct_lineitem  
**Description:** Total revenue generated from line items, aggregated monthly. This is a core North Star metric for measuring overall business performance.  
**Formula:** SUM(fct_lineitem.lineitem_revenue)  
**Notes:** Promoted to L0 North Star metric. Assumes 'lineitem_revenue' is the correct column for revenue calculation.  
