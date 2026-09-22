select 1 as failure
where not exists (
    select 1
    from {{ ref('genre_decade_summary') }}
)
