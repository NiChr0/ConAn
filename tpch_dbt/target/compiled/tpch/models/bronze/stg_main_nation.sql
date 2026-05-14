-- Bronze: Staging from source (explicit columns + type casts)
select
    n_nationkey,
    n_name,
    n_regionkey,
    n_comment
from "tpch"."main"."nation"