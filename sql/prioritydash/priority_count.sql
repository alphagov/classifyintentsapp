select priority, count(*), (select * from now()) as date from priority group by priority order by priority;
\watch 1
