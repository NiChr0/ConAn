-- Bronze: Staging from source (explicit columns + type casts)
select
    l_orderkey,
    l_partkey,
    l_suppkey,
    l_linenumber,
    l_quantity,
    l_extendedprice,
    l_discount,
    l_tax,
    l_returnflag,
    l_linestatus,
    l_shipdate::date as l_shipdate,
    l_commitdate::date as l_commitdate,
    l_receiptdate::date as l_receiptdate,
    l_shipinstruct,
    l_shipmode,
    l_comment
from {{ source('main', 'lineitem') }}
