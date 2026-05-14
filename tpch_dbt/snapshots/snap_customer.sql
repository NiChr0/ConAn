{% snapshot snap_customer %}

{{
    config(
        target_schema='snapshots',
        unique_key='c_custkey',
        strategy='check',
        check_cols=['c_name', 'c_address', 'c_nationkey', 'c_phone', 'c_acctbal', 'c_mktsegment', 'c_comment'],
    )
}}

select * from {{ source('main', 'customer') }}

{% endsnapshot %}
