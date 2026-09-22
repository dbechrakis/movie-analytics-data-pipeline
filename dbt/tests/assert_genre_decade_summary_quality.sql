select *
from {{ ref('genre_decade_summary') }}
where total_films <= 0
   or avg_rating < 0
   or avg_rating > 10
   or avg_roi is null
   or (genre_name, decade) in (
       select genre_name, decade
       from {{ ref('genre_decade_summary') }}
       group by genre_name, decade
       having count(*) > 1
   )
