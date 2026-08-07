{{ config(materialized='view') }}

with source_movies as (
    select * from {{ source('raw', 'movies') }}
),

cleaned as (
    select
        id::bigint as movie_id,
        nullif(title, '') as title,
        nullif(release_date, '')::date as release_date,
        extract(year from nullif(release_date, '')::date)::integer as release_year,
        genre_ids,
        budget::numeric as budget,
        revenue::numeric as revenue,
        vote_average::numeric as vote_average,
        vote_count::integer as vote_count,
        popularity::numeric as popularity,
        source,
        ingested_at::timestamptz as ingested_at
    from source_movies
)

select
    movie_id,
    title,
    release_date,
    release_year,
    genre_ids,
    budget,
    revenue,
    vote_average,
    vote_count,
    popularity,
    round(((revenue - budget) / nullif(budget, 0))::numeric, 4) as roi,
    source,
    ingested_at
from cleaned
where title is not null
  and release_date is not null
  and budget > 0
  and revenue > 0
  and vote_average between 0 and 10
