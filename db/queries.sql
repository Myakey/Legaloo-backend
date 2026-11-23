-- Reference queries (tested against schema.sql + seed.sql). Use them in repositories/ with asyncpg.
-- psql style: :'uid' is the user id. In asyncpg, replace with $1.
-- Rules: courses are independent (each course's first unfinished level is ACTIVE); levels unlock in order.
-- Current course = course of the most recent completion that still has unfinished levels,
-- else the lowest-numbered course with unfinished levels, else course 1.

-- courses for user
with done as (
  select course_id, level_position, completed_at from level_completions where user_id = :'uid'
),
cur as (
  select coalesce(
    (select d.course_id from done d
       join (select course_id, count(*) n from levels group by course_id) t using (course_id)
       where (select count(*) from done d2 where d2.course_id = d.course_id) < t.n
       order by d.completed_at desc limit 1),
    (select c.id from courses c where exists (select 1 from levels l where l.course_id=c.id
        and not exists (select 1 from done d where d.course_id=l.course_id and d.level_position=l.position)) order by c.number limit 1),
    (select min(id) from courses)) as course_id
)
select c.id, c.number, c.title, c.unit_label,
  round((count(d.level_position)::numeric / count(l.position)),2) as progress,
  c.id = (select course_id from cur) as is_current,
  json_agg(json_build_object('id', l.position, 'type', l.type, 'state',
     case when d.level_position is not null then 'COMPLETED'
          when l.position = (select min(l2.position) from levels l2 where l2.course_id=c.id
               and not exists (select 1 from done d3 where d3.course_id=l2.course_id and d3.level_position=l2.position)) then 'ACTIVE'
          else 'LOCKED' end) order by l.position) as levels
from courses c join levels l on l.course_id=c.id
left join done d on d.course_id=l.course_id and d.level_position=l.position
group by c.id order by c.number;

-- streak
with today as (select (now() at time zone 'Asia/Jakarta')::date d),
goal as (select daily_goal_minutes g from users where id = :'uid'),
met as (select study_date from study_log, goal where user_id = :'uid' and minutes >= g),
start as (select case when exists (select 1 from met, today where study_date = today.d) then (select d from today) else (select d from today) - 1 end s)
select count(*) as streak from (
  select study_date, (select s from start) - study_date as off,
         row_number() over (order by study_date desc) - 1 as rn
  from met where study_date <= (select s from start)
) x where off = rn;
