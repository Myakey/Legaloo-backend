-- Legaloo database schema (Supabase Postgres).
-- Run once in the Supabase SQL editor, then run seed.sql.
-- Safe to re-run: every statement is idempotent.
--
-- The FastAPI backend connects as the `postgres` role via DATABASE_URL, which bypasses RLS.
-- RLS is enabled with NO policies so the public Supabase REST API (anon key) cannot read or
-- write these tables. Do not add policies unless the app starts talking to Supabase directly.

create extension if not exists vector;

-- ---------------------------------------------------------------- users
create table if not exists users (
  id                 uuid primary key default gen_random_uuid(),
  name               text not null,
  email              text not null,
  password_hash      text not null,               -- bcrypt, never plaintext
  daily_goal_minutes int  not null default 10 check (daily_goal_minutes > 0),
  created_at         timestamptz not null default now()
);
create unique index if not exists users_email_lower_key on users (lower(email));

-- ---------------------------------------------------------------- curriculum
create table if not exists courses (
  id          int  primary key,                   -- stable ids 1..n, matches the app
  number      int  not null unique,               -- display order / "Kursus N"
  title       text not null,
  unit_number int  not null default 1,
  unit_label  text not null                       -- e.g. 'KURSUS 1, UNIT 2'
);

create table if not exists levels (
  course_id int  not null references courses(id) on delete cascade,
  position  int  not null check (position > 0),   -- exposed to the app as LevelNode.id
  type      text not null check (type in ('LESSON', 'PRACTICE')),
  title     text not null,
  primary key (course_id, position)
);

create table if not exists lesson_steps (
  id             bigserial primary key,
  course_id      int  not null,
  level_position int  not null,
  position       int  not null check (position > 0),
  kind           text not null check (kind in ('READ', 'EXAMPLES', 'QUIZ')),
  mode_label     text not null,                   -- 'MODE BACA' | 'MODE KUIS'
  title          text,
  content        jsonb not null,                  -- shape depends on kind, see CLAUDE.md
  mascot_message text,                            -- what "Pak Singa" says on this step
  foreign key (course_id, level_position) references levels(course_id, position) on delete cascade,
  unique (course_id, level_position, position)
);

-- ---------------------------------------------------------------- per-user progress
create table if not exists level_completions (
  user_id        uuid not null references users(id) on delete cascade,
  course_id      int  not null,
  level_position int  not null,
  correct        boolean not null default true,
  completed_at   timestamptz not null default now(),
  primary key (user_id, course_id, level_position),
  foreign key (course_id, level_position) references levels(course_id, position) on delete cascade
);
create index if not exists level_completions_user_recent on level_completions (user_id, completed_at desc);

create table if not exists study_log (
  user_id    uuid not null references users(id) on delete cascade,
  study_date date not null,                       -- calendar day in Asia/Jakarta
  minutes    int  not null default 0 check (minutes >= 0),
  primary key (user_id, study_date)
);

-- ---------------------------------------------------------------- RAG
create table if not exists documents (
  id        bigserial primary key,
  content   text not null,
  source    text not null,                        -- citable name, e.g. 'UU No. 22 Tahun 2009, Pasal 106'
  embedding vector(768)                           -- gemini-embedding-001 with outputDimensionality=768
);
create index if not exists documents_embedding_hnsw on documents using hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------- lock down the public REST API
alter table users             enable row level security;
alter table courses           enable row level security;
alter table levels            enable row level security;
alter table lesson_steps      enable row level security;
alter table level_completions enable row level security;
alter table study_log         enable row level security;
alter table documents         enable row level security;
