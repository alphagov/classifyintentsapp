select respondent_id, users.username, codes.code, project_codes.project_code, pii, date_coded 
from classified 
left join codes 
on (classified.code_id=codes.code_id) 
left join project_codes 
on (classified.project_code_id = project_codes.project_code_id) 
left join users 
on (classified.coder_id=users.id) 
order by date_coded 
desc limit 10;
\watch 0.2
