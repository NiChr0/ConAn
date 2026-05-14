{% snapshot snap_supplier %}

{{
    config(
        target_schema='snapshots',
        unique_key='s_suppkey',
        strategy='check',
        check_cols=['s_name', 's_address', 's_nationkey', 's_phone', 's_acctbal', 's_comment'],
    )
}}

select * from {{ source('main', 'supplier') }}

{% endsnapshot %}
