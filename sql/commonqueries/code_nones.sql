with cte as (select respondent_id 
from raw 
where comment_why_you_came is Null
and comment_where_for_help is Null
and comment_further_comments is Null
)
insert into classified (respondent_id, coder_id, code_id, project_code_id,pii,date_coded)
select respondent_id,
        (select id from users where username='automated') as coder_id,
        (select code_id from codes where code='none')  as code_id,
        (select project_code_id from project_codes where project_code='none') as project_code_id,
        'f' as pii,
        (select * from now()) as date_coded
 from cte;

