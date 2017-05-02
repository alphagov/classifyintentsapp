with cte as (select respondent_id 
from raw 
where comment_why_you_came is Null
and comment_where_for_help is Null
and comment_further_comments is Null
)
insert into classified (respondent_id, coder_id, code_id, project_code_id,pii,date_coded)
select respondent_id,
        2 as coder_id,
        0 as code_id,
        0 as project_code_id,
        'f' as pii,
        (select * from now()) as date_coded
 from cte;

