{% macro incremental_date_filter(filter_col, max_col=none) %}
    {% if is_incremental() %}
    where (
        {{ filter_col }} > (
            select max({{ max_col or filter_col }})
                - interval '{{ var("incremental_lookback_days", 7) }} days'
            from {{ this }}
        )
        or {{ filter_col }} is null
    )
    {% endif %}
{% endmacro %}
