-- Bronze: Staging from source (explicit columns + type casts)
select
    c_custkey,
    c_name,
    c_address,
    c_nationkey,
    c_phone,
    c_acctbal,
    c_mktsegment,
    c_comment
from "tpch"."main"."customer"