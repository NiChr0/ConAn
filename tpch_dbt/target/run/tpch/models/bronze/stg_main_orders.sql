
  
  create view "tpch"."main"."stg_main_orders__dbt_tmp" as (
    -- Bronze: Staging from source (explicit columns + type casts)
select
    o_orderkey,
    o_custkey,
    o_orderstatus,
    o_totalprice,
    o_orderdate::date as o_orderdate,
    o_orderpriority,
    o_clerk,
    o_shippriority,
    o_comment
from "tpch"."main"."orders"
  );
