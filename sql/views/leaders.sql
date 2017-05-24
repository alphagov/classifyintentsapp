-- Use only in-line comments in this file, as they will be
-- identified and removed by query_loader().
-- Remove pre-existing table and view which may have been 
-- created by db.create_all()
create view leaders as (
    with cte as (
        select coder_id, count(*) as n 
        from Classified 
        group by coder_id
    )
    select row_number() over (order by cte.n desc) as rank, users.username, cte.n 
    from cte 
    left join users 
    on users.id=cte.coder_id limit 5
    );

create view daily_leaders as (
    with cte as (
    select coder_id, count(*) as n
    from classified 
    where date_coded > (select date_trunc('day', now()))
    group by coder_id
    )
    select row_number() over (order by cte.n desc) as rank, users.username, cte.n 
    from cte 
    left join users 
    on users.id=cte.coder_id limit 5
    );

create view weekly_leaders as (
    with cte as (
    select coder_id, count(*) as n
    from classified 
    where date_coded > (select date_trunc('week', now()) -INTERVAL '1 day')
    group by coder_id
    )
    select row_number() over (order by cte.n desc) as rank, users.username, cte.n 
    from cte 
    left join users 
    on users.id=cte.coder_id limit 5
    );
