-- Use only in-line comments in this file, as they will be
-- identified and removed by query_loader().
-- Start with the join of raw to classified
create view priority as (
with codes_join 
as (select raw.respondent_id, code_id, count(*) as max
from classified a
full outer join raw
on (a.respondent_id = raw.respondent_id)
-- If we need to prioritise a particular date period, if can be
-- done here by specifying a date range
--where raw.start_date > '2017-04-21'
group by raw.respondent_id, a.code_id
order by raw.start_date desc
-- Limit to the most recent 5000 surveys. This may be required
-- otherwise the prioritisation view takes about a second to be
-- reproduced (and will get slower as the db gets bigger).
limit 5000
),
-- Now calculate how many times a survey has been classified
total_codes as (
select  respondent_id, sum(max) as total
from codes_join
group by respondent_id
),
-- Join these together and calculate the ratio of the two
-- i.e. the number of times a single code has been applied
-- divided by the total number of times survey was coded.
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
-- Get the maximum ratio and total, aggregating up to the survey level
survey_level_ratio as (
select respondent_id, max(code_id) as coded, max(max) as max, max(ratio) as ratio, max(total) as total 
from ratio_table
group by respondent_id
),
-- Identify which surveys were already classified automatically.
-- This will generally be surveys which do not have any free text
-- content, or easily identifiable 'ok' cases.
-- See: https://gdsdata.blog.gov.uk/2016/12/20/using-machine-learning-to-classify-user-comments-on-gov-uk/
-- and: https://github.com/ukgovdatascience/classifyintentspipe
automated as (
select distinct respondent_id, 1 as automated
from classified 
left join users 
on (classified.coder_id = users.id)
where users.username = 'automated'
),
-- Create table of who coded what and identify whether a survey has been
-- tagged as containing pii.
who_coded_what as (
select  respondent_id, 
        array_agg(distinct classified.coder_id) as coders,
        count(pii or null) as pii
from classified
group by respondent_id
),
final_priority as (
-- Bind it all together,
-- Priority is controlled with the case when statement here
-- The lower the number, the higher the priority.
select  slr.respondent_id, 
        date_trunc('month', raw.start_date) as month,
        slr.max,
        slr.ratio,
        slr.total,
        wcw.coders,
        wcw.pii,
        case 
            -- When there is pii
            when wcw.pii > 0 then 8
            -- When the survey was coded automatically
            when automated.automated = 1 and slr.total = 1 then 6
            -- When there is a majority, but only two people agreed so far
            -- When five people have coded and still agreement, then 9 (gold standard)
            when (slr.ratio > 0.5 and slr.total > 1 and slr.total < 5)
            or (slr.ratio = 1 and slr.total = 2) then 3
            -- When there is not a majority and five or fewer codes applied (still undecided)
            when slr.ratio <= 0.5 and slr.total <= 4 then 1
            -- When the survey has not been coded before (new survey)
            when slr.total = 1 and slr.ratio = 1 and slr.coded is null then 2
            -- When the survey has been coded just once (still undecided)
            when slr.total = 1 and slr.ratio = 1 and slr.coded is not null then 1
            -- When the survey has been classified 5 times, with no decision (difficult to code)
            when slr.total > 4 and slr.ratio < 0.5 then 7
            else 9
        end as priority
from survey_level_ratio slr
left join raw
on (slr.respondent_id=raw.respondent_id)
left join who_coded_what wcw
on (slr.respondent_id=wcw.respondent_id)
left join automated 
on (slr.respondent_id=automated.respondent_id)
order by month desc, priority
)
select * from final_priority);

