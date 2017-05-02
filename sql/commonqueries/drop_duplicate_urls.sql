/*
Looks for duplicates in the urls table and deletes
if the full_url, page, org0, and section0 columns 
have not changed.
*/

delete from urls
where url_id in (
select url_id
from (
select url_id,
       row_number() OVER (partition by full_url, page, org0, section0 order by url_id) as rnum
from urls) t
where t.rnum > 1);

