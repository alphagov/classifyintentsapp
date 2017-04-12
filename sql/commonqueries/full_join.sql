
create view full_join 
as select * from classified c left outer join raw 
on (c.respondent_id = raw.respondent_id) 
left outer join urls 
on (raw.full_url = urls.full_url);
