{{ config(materialized='table') }}

with movies as (
    select * from {{ ref('stg_movies') }}
),

movie_genres as (
    select
        movie_id,
        jsonb_array_elements_text(genre_ids::jsonb)::bigint as genre_id
    from movies
),

genres as (
    select
        id::bigint as genre_id,
        name as genre_name
    from {{ source('raw', 'genres') }}
),

joined as (
    select
        genres.genre_name,
        (floor(movies.release_year / 10) * 10)::integer as decade,
        movies.movie_id,
        movies.vote_average,
        movies.roi
    from movies
    inner join movie_genres
        on movies.movie_id = movie_genres.movie_id
    inner join genres
        on movie_genres.genre_id = genres.genre_id
)

select
    genre_name,
    decade,
    count(distinct movie_id)::integer as total_films,
    round(avg(vote_average)::numeric, 2) as avg_rating,
    round(avg(roi)::numeric, 4) as avg_roi
from joined
group by genre_name, decade
