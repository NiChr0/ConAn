
  
  create view "tpch"."main"."stg_main_partsupp__dbt_tmp" as (
    -- Bronze: Staging from source (explicit columns + type casts)
select
    ps_partkey,
    ps_suppkey,
    ps_availqty,
    ps_supplycost,
    ps_comment
from "tpch"."main"."partsupp"
  );
