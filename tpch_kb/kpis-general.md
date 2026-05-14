# KPIs — General

## GEN-001: agg_daily_lineitem_quantity
**Tier:** L1  
**Maturity:** Validated  
**Confidence Ceiling:** 90%  
**Source Table:** fct_lineitem  
**Description:** Tracks the total aggregated quantity of line items sold daily, providing a core measure of sales volume and operational activity.  
**Formula:** SUM(l_quantity)  
**Notes:** This metric is a core operational indicator (L1) tracking sales volume. The formula uses the SUM aggregation on the line item quantity column.  
