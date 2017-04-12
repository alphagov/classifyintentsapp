/*
Priority:

* Surveys with no majority
* Surveys with fewer than 3 coders
* Surveys with no codes

Need to make sure coders do not see surveys they have already coded.

Logic here:

*   Join the classfied with the raw table and then count the instances 
    of each respondent_id. If n = 1, then it only appears in the raw
    table, not the classified table, and so has not yet been classified.
    Each additional n is an additional classification.
*   Using this joined (codes_join) table as a common table expression, 
    then calculate the count for each code applied to each respondent_id.
    This is the max_codes cte, do the same for the total number of codes 
    in the total_codes cte.
*   Divide the max codes by the total codes to give ratio. If the ratio is
    greater than 0.5, then we know that there is a majority vote for a given
    code.
*   Calculate a survey priority with the following steps in the priority_table cte
        * if ratio <= 0.5: priority = 1
        * if ratio > 0.5 and total < 3: priority = 2
        * if code_id is null: priority = 3
*   Select out the distinct respondent_ids and priorities into the view priority_table
    
*/


-- Start with the join or raw to classified
create view priority_check as (
with codes_join 
as (select raw.respondent_id, code_id, count(*) as max
from classified a
full outer join raw
on (a.respondent_id = raw.respondent_id)
group by (raw.respondent_id, a.code_id)
),
-- Now calculate how many times a survey has been classified
total_codes as (
select respondent_id, sum(max) as total
from codes_join
group by respondent_id
),
-- Join these together and calculate the ratio of the two
ratio_table as(
select codes_join.respondent_id, 
        code_id, 
        max, 
        total, 
        cast(max as real)/cast(total as real) as ratio,
        case 
            when cast(max as real)/cast(total as real) > 0.5 and total > 1 and total < 3 then 2
            when cast(max as real)/cast(total as real) <= 0.5 then 1
            when code_id is null then 3
            else 4
        end as priority
from codes_join
left join
total_codes on 
codes_join.respondent_id = total_codes.respondent_id
order by codes_join.respondent_id)
-- Finally get just the respondent_id and the priority
-- Also join in the date the survey was started so that
-- this can be used to prioritise by date. Note that this join seems to be 
-- quite slow, and could be removed in favour of a lookup in sqlalchemy
select rt.respondent_id, max(rt.ratio) as max_ratio, max(rt.total) as max_total, max(rt.max) as max_max, min(rt.priority) as min_priority
from ratio_table rt
group by rt.respondent_id
order by min_priority
);
