"""Streak, daily minutes and completions.

"Today" is always computed in SQL as (now() at time zone 'Asia/Jakarta')::date,
never from the Python clock (Vercel runs in UTC). The streak query is ported
verbatim from db/queries.sql.
"""

from dataclasses import dataclass

import asyncpg

from ..db.session import get_pool

_STREAK_SQL = """
with today as (select (now() at time zone 'Asia/Jakarta')::date d),
goal as (select daily_goal_minutes g from users where id = $1::uuid),
met as (select study_date from study_log, goal where user_id = $1::uuid and minutes >= g),
start as (select case when exists (select 1 from met, today where study_date = today.d) then (select d from today) else (select d from today) - 1 end s)
select count(*) as streak from (
  select study_date, (select s from start) - study_date as off,
         row_number() over (order by study_date desc) - 1 as rn
  from met where study_date <= (select s from start)
) x where off = rn
"""

# Monday..Sunday of the current WIB week. Future days have no study_log rows,
# and are forced to false anyway.
_WEEK_SQL = """
with today as (select (now() at time zone 'Asia/Jakarta')::date d),
goal as (select daily_goal_minutes g from users where id = $1::uuid),
week as (
  select today.d - (extract(isodow from today.d)::int - 1) + i as day, today.d as today
  from today, generate_series(0, 6) as i
)
select w.day, w.day = w.today as is_today, coalesce(sl.minutes, 0) as minutes,
       (w.day <= w.today and coalesce(sl.minutes, 0) >= goal.g) as completed
from week w cross join goal
left join study_log sl on sl.user_id = $1::uuid and sl.study_date = w.day
order by w.day
"""

_UPSERT_COMPLETION_SQL = """
insert into level_completions (user_id, course_id, level_position, correct, completed_at)
values ($1::uuid, $2, $3, $4, now())
on conflict (user_id, course_id, level_position)
do update set correct = excluded.correct, completed_at = excluded.completed_at
"""

_ADD_MINUTES_SQL = """
insert into study_log (user_id, study_date, minutes)
values ($1::uuid, (now() at time zone 'Asia/Jakarta')::date, $2)
on conflict (user_id, study_date) do update set minutes = study_log.minutes + excluded.minutes
"""


@dataclass(frozen=True)
class DayRow:
    is_today: bool
    minutes: int
    completed: bool


@dataclass(frozen=True)
class StudyStats:
    streak: int
    week: list[DayRow]  # Monday first, always 7 entries

    @property
    def minutes_today(self) -> int:
        return next((d.minutes for d in self.week if d.is_today), 0)


async def get_stats(user_id: str) -> StudyStats:
    async with (await get_pool()).acquire() as conn:
        streak = await conn.fetchval(_STREAK_SQL, user_id)
        rows = await conn.fetch(_WEEK_SQL, user_id)
    week = [
        DayRow(is_today=r["is_today"], minutes=r["minutes"], completed=r["completed"])
        for r in rows
    ]
    return StudyStats(streak=int(streak or 0), week=week)


async def record_completion(
    conn: asyncpg.Connection,
    user_id: str,
    course_id: int,
    level_position: int,
    correct: bool,
    minutes: int,
) -> None:
    """Call inside a transaction: the completion and the minutes land together."""
    await conn.execute(
        _UPSERT_COMPLETION_SQL, user_id, course_id, level_position, correct
    )
    await conn.execute(_ADD_MINUTES_SQL, user_id, minutes)
