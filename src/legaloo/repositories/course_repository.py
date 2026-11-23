"""Per-user course/level state. Ported from db/queries.sql ("courses for user").

State, progress and the current course are computed here on every request,
never stored. Differences from queries.sql are additive only: the level
`title` and `c.unit_number` are selected, and `$2` optionally filters to one
course (the `cur` CTE still looks at all courses, so `is_current` is unchanged).
"""

import json
from dataclasses import dataclass

import asyncpg

from ..db.session import get_pool


@dataclass(frozen=True)
class LevelState:
    id: int
    type: str
    state: str
    title: str


@dataclass(frozen=True)
class CourseState:
    id: int
    number: int
    title: str
    unit_number: int
    unit_label: str
    progress: float
    is_current: bool
    levels: list[LevelState]


_COURSES_SQL = """
with done as (
  select course_id, level_position, completed_at from level_completions where user_id = $1::uuid
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
select c.id, c.number, c.title, c.unit_number, c.unit_label,
  round((count(d.level_position)::numeric / count(l.position)),2) as progress,
  c.id = (select course_id from cur) as is_current,
  json_agg(json_build_object('id', l.position, 'type', l.type, 'title', l.title, 'state',
     case when d.level_position is not null then 'COMPLETED'
          when l.position = (select min(l2.position) from levels l2 where l2.course_id=c.id
               and not exists (select 1 from done d3 where d3.course_id=l2.course_id and d3.level_position=l2.position)) then 'ACTIVE'
          else 'LOCKED' end) order by l.position) as levels
from courses c join levels l on l.course_id=c.id
left join done d on d.course_id=l.course_id and d.level_position=l.position
where ($2::int is null or c.id = $2::int)
group by c.id order by c.number
"""


def _course(r: asyncpg.Record) -> CourseState:
    levels = json.loads(r["levels"]) if isinstance(r["levels"], str) else r["levels"]
    return CourseState(
        id=r["id"],
        number=r["number"],
        title=r["title"],
        unit_number=r["unit_number"],
        unit_label=r["unit_label"],
        progress=float(r["progress"]),
        is_current=r["is_current"],
        levels=[LevelState(**lv) for lv in levels],
    )


async def list_for_user(
    user_id: str, conn: asyncpg.Connection | None = None
) -> list[CourseState]:
    if conn is not None:
        rows = await conn.fetch(_COURSES_SQL, user_id, None)
    else:
        async with (await get_pool()).acquire() as c:
            rows = await c.fetch(_COURSES_SQL, user_id, None)
    return [_course(r) for r in rows]


async def get_for_user(
    user_id: str, course_id: int, conn: asyncpg.Connection | None = None
) -> CourseState | None:
    if conn is not None:
        r = await conn.fetchrow(_COURSES_SQL, user_id, course_id)
    else:
        async with (await get_pool()).acquire() as c:
            r = await c.fetchrow(_COURSES_SQL, user_id, course_id)
    return _course(r) if r is not None else None
