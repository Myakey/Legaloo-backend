"""Lesson content: a level's header and its ordered steps."""

import json
from dataclasses import dataclass
from typing import Any

from ..db.session import get_pool


@dataclass(frozen=True)
class StepRow:
    position: int
    kind: str
    mode_label: str
    title: str | None
    mascot_message: str | None
    content: dict[str, Any]


_STEPS_SQL = """
select position, kind, mode_label, title, mascot_message, content::text as content
from lesson_steps
where course_id = $1 and level_position = $2
order by position
"""

# Used by scripts/ingest_lessons.py to build the demo chat corpus.
_READ_PARAGRAPHS_SQL = """
select l.title as level_title, p.paragraph
from lesson_steps s
join levels l on l.course_id = s.course_id and l.position = s.level_position
cross join lateral jsonb_array_elements_text(s.content -> 'paragraphs') as p(paragraph)
where s.kind = 'READ'
order by s.course_id, s.level_position, s.position
"""


async def get_steps(course_id: int, level_position: int) -> list[StepRow]:
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(_STEPS_SQL, course_id, level_position)
    return [
        StepRow(
            position=r["position"],
            kind=r["kind"],
            mode_label=r["mode_label"],
            title=r["title"],
            mascot_message=r["mascot_message"],
            content=json.loads(r["content"]),
        )
        for r in rows
    ]


async def list_read_paragraphs() -> list[tuple[str, str]]:
    """(level title, paragraph) for every paragraph of every READ step."""
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(_READ_PARAGRAPHS_SQL)
    return [(r["level_title"], r["paragraph"]) for r in rows]
