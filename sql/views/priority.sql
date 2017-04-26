/*
---
name: Priority View
filename: priority.sql
logic:
    - Join the classfied with the raw table and count total of each code
      applied to each survey (respondent_id) to give the codes_join cte.
    - Calculate the total number of codes applied to each survey to give
      total_codes cte.
    - Join these two ctes and calculate the ratio codes applied:
      count of each code/total number of codes.
    - Get the maximum ratio, total, and max count for any code in the 
      survey_level_ratio cte.
    - Apply prioritisation rules to the survey_level_ratio cte:
        - When not coded: 3
        - When coded once: 1
        - When coded without majority (up to total 5): 1
        - When coded without majority (more than 5): 8
        - When coded with majority but less than 3 coders: 2
        - When majority found: 9
    - Join in start_date from raw, and order by priority and start_date
---    
*/
drop view if exists priority; 
-- Start with the join or raw to classified
create view priority as (
with codes_join 
as (select raw.respondent_id, code_id, count(*) as max
from classified a
full outer join raw
on (a.respondent_id = raw.respondent_id)
--where raw.start_date > '2017-04-21'
group by (raw.respondent_id, a.code_id)
order by raw.start_date desc
limit 6000
),
-- Now calculate how many times a survey has been classified
total_codes as (
select  respondent_id, sum(max) as total
from codes_join
group by respondent_id
),
-- Join these together and calculate the ratio of the two
ratio_table as(
select codes_join.respondent_id, 
        code_id, 
        max, 
        total, 
        cast(max as real)/cast(total as real) as ratio
from codes_join
left join
total_codes on 
(codes_join.respondent_id=total_codes.respondent_id)
),
-- Get the maximum ratio and total, and aggregate up to the survey level
survey_level_ratio as (
select respondent_id, max(code_id) as coded, max(max) as max, max(ratio) as ratio, max(total) as total 
from ratio_table
group by respondent_id
),
automated as (
select distinct respondent_id, 1 as automated
from classified 
left join users 
on (classified.coder_id = users.id)
where users.username = 'automated'
),
who_coded_what as (
select  respondent_id, 
        array_agg(distinct classified.coder_id) as coders,
        count(pii or null) as pii
from classified
group by respondent_id
),
final_priority as (
-- Priority is controlled with the case when statement here
-- The lower the number, the higher the priority.
select  slr.respondent_id, 
        raw.start_date, 
        slr.max,
        slr.ratio,
        slr.total,
        wcw.coders,
        wcw.pii,
        case 
            when automated.automated = 1 then 4
            when wcw.pii > 0 then 8
            -- When there is a majority, but less than 3 people coded
            when (slr.ratio > 0.5 and slr.total > 1 and slr.total < 5)
            or (slr.ratio = 1 and slr.total = 2) then 3
            -- When there is not a majority and five or fewer codes applied
            when slr.ratio <= 0.5 and slr.total <= 5 then 1
            -- When the survey has not been coded before
            when slr.total = 1 and slr.ratio = 1 and slr.coded is null then 2
            -- When the survey has been coded just once
            when slr.total = 1 and slr.ratio = 1 and slr.coded is not null then 1
            -- When the survey is difficult to code (no majority after 5)
            when slr.total > 5 and slr.ratio < 0.5 then 7
            else 9
        end as priority
from survey_level_ratio slr
left join raw
on (slr.respondent_id=raw.respondent_id)
left join who_coded_what wcw
on (slr.respondent_id=wcw.respondent_id)
left join automated 
on (slr.respondent_id=automated.respondent_id)
order by priority, raw.start_date desc, respondent_id
)
select * from final_priority where priority < 10);

