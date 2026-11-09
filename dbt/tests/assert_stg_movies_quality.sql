select *
from {{ ref('stg_movies') }}
where vote_average < 0
   or vote_average > 10
   or budget < {{ var('min_reported_usd') }}
   or revenue < {{ var('min_reported_usd') }}
   or roi is null
