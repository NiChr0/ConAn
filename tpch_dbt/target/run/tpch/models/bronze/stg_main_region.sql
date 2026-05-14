
  
  create view "tpch"."main"."stg_main_region__dbt_tmp" as (
    -- Bronze: Staging from source (explicit columns + type casts)
select
    r_regionkey,
    r_name,
    r_comment
from "tpch"."main"."region"
  );
