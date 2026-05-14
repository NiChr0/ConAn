-- Bronze: Staging from source (explicit columns + type casts)
select
    r_regionkey,
    r_name,
    r_comment
from "tpch"."main"."region"