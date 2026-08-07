select *
from {{ ref('stg_movies') }}
where vote_average < 0
   or vote_average > 10
   or budget <= 0
   or revenue <= 0
   or roi is null
