-- Bronze: Staging from source (explicit columns + type casts)
select
    s_suppkey,
    s_name,
    s_address,
    s_nationkey,
    s_phone,
    s_acctbal,
    s_comment
from "tpch"."main"."supplier"