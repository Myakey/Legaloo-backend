# Legaloo backend: handover for the Android app

Status 2026-11-23: auth, courses, progress, lessons and level completion are implemented and tested against the real Supabase database. The chat (`POST /chat`) has the endpoint, but it is **not ready for the demo yet** (Gemini key and lesson corpus still to do).

## Base URL

| Where the app runs | Base URL |
|---|---|
| Android emulator, backend in WSL on the same PC | `http://10.0.2.2:8000` |
| Physical phone over USB (`adb reverse tcp:8000 tcp:8000`) | `http://localhost:8000` |
| Production (after Vercel deploy) | `https://<project>.vercel.app` (TBD) |

Start the backend with `uv run uvicorn legaloo.main:app --reload --host 0.0.0.0 --port 8000`. Interactive docs: `<base>/docs`.

App setup needed:
- `<uses-permission android:name="android.permission.INTERNET" />` in the manifest.
- Plain `http://` dev URLs need a **debug-only** `networkSecurityConfig` that allows cleartext.
- JSON parser: `Json { ignoreUnknownKeys = true }` (the API sends a few extra fields, such as level `title`).

## Conventions

- JSON field names are **camelCase**, matching `data/Models.kt`. Enums are uppercase strings matching the Kotlin enum names.
- Every endpoint except `/auth/*`, `/health` and `/chat` needs the header `Authorization: Bearer <token>`.
- Tokens last 30 days. There is no refresh endpoint. On any **401**, clear the stored token and go to the login screen.
- **Every error** has the same body:

  ```json
  { "detail": "Pesan untuk pengguna", "field": "name" | "email" | "password" | null }
  ```

  Show `detail` under the matching form field, or as a form/snackbar error when `field` is `null`. Messages are already in Indonesian and ready to display.

## Endpoints

| Method | Path | Auth | Replaces in the app |
|---|---|---|---|
| POST | `/auth/register` | – | `AuthRepository.register` |
| POST | `/auth/login` | – | `AuthRepository.login` |
| GET | `/me` | Bearer | current user (profile) |
| GET | `/me/progress` | Bearer | `HomeViewModel` / `DummyData.userProgress` |
| GET | `/courses` | Bearer | `CourseViewModel` / `DummyData.courses` |
| GET | `/courses/{courseId}` | Bearer | one course |
| GET | `/courses/{courseId}/levels/{levelId}/lesson` | Bearer | hard-coded `CourseMaterial1Screen` |
| POST | `/courses/{courseId}/levels/{levelId}/complete` | Bearer | finishing a level |
| POST | `/chat` | – | "Tanya Legaloo" (not ready yet) |
| GET | `/health` | – | server check |

`levelId` is the level's position within its course (1..n), the same as `LevelNode.id`.

### POST /auth/register

```json
{ "name": "Andi Wijaya", "email": "andi@example.com", "password": "rahasia123" }
```

**201**:

```json
{ "token": "eyJ...", "user": { "id": "uuid", "name": "Andi Wijaya", "email": "andi@example.com" } }
```

The name and email are trimmed, and the email is stored lowercase. Validation matches `AuthValidator.kt`. The first failing field is returned with **422**:

| field | message |
|---|---|
| name | `Nama wajib diisi` / `Nama minimal 3 karakter` / `Nama hanya boleh berisi huruf dan spasi` |
| email | `Email wajib diisi` / `Format email tidak valid` |
| password | `Kata sandi wajib diisi` / `Kata sandi minimal 8 karakter` / `Kata sandi harus berisi huruf dan angka` |

Email already registered (case-insensitive) → **409** `Email sudah terdaftar`, `field: "email"`.

### POST /auth/login

```json
{ "email": "budi@legaloo.id", "password": "legaloo123" }
```

**200**: same body as register. Wrong email or password → **401** `Email atau kata sandi salah`, `field: null`. Empty fields or a bad email format → 422, as for register.

### GET /me

```json
{ "id": "uuid", "name": "Budi Santoso", "email": "budi@legaloo.id", "dailyGoalMinutes": 10 }
```

### GET /me/progress

```json
{ "userName": "Budi Santoso", "streakCount": 7, "minutesStudied": 6, "dailyGoalMinutes": 10,
  "week": [ { "label": "S", "completed": true }, { "label": "S", "completed": false },
            { "label": "R", "completed": false }, { "label": "K", "completed": false },
            { "label": "J", "completed": false }, { "label": "S", "completed": false },
            { "label": "M", "completed": false } ],
  "currentCourseId": 1, "currentUnitNumber": 2 }
```

- `week` is always 7 items, Monday to Sunday. `completed` means the daily goal was met that day. Future days are `false`.
- `minutesStudied` counts today only (WIB). The streak doesn't break until the day is over.

### GET /courses and GET /courses/{courseId}

`/courses` returns a list ordered by `number`. `/courses/{id}` returns one course, or **404** `Kursus tidak ditemukan`.

```json
{ "id": 1, "number": 1, "title": "Hak dan Kewajiban", "progress": 0.4,
  "unitLabel": "KURSUS 1, UNIT 2", "isCurrent": true,
  "levels": [ { "id": 1, "type": "LESSON",   "state": "COMPLETED", "title": "Apa Itu Hak?" },
              { "id": 3, "type": "LESSON",   "state": "ACTIVE",    "title": "..." },
              { "id": 5, "type": "PRACTICE", "state": "LOCKED",    "title": "..." } ] }
```

- `type`: `LESSON` | `PRACTICE`. `state`: `COMPLETED` | `ACTIVE` | `LOCKED`.
- `progress` is a float from 0 to 1. Exactly one course has `isCurrent: true`.
- Each course is independent: the first unfinished level in each course is `ACTIVE`.
- State is computed by the server. Don't cache it; re-fetch after completing a level (or use the `complete` response).

### GET /courses/{courseId}/levels/{levelId}/lesson

```json
{ "courseId": 4, "levelId": 1, "type": "LESSON", "title": "Rambu dan Lampu Lalu Lintas",
  "steps": [
    { "position": 1, "kind": "READ", "modeLabel": "MODE BACA", "title": "...", "mascotMessage": "Ayo kita lanjut!",
      "content": { "paragraphs": ["...", "..."] } },
    { "position": 2, "kind": "EXAMPLES", "modeLabel": "MODE BACA", "title": "Menyeberang dengan Aman", "mascotMessage": "...",
      "content": { "examples": [ { "label": "CONTOH BAIK", "tone": "GOOD", "caption": "...", "illustration": "CROSSING_GREEN" } ] } },
    { "position": 3, "kind": "QUIZ", "modeLabel": "MODE KUIS", "title": null, "mascotMessage": "Pilih jawabanmu!",
      "content": { "question": "...", "options": [ { "text": "...", "correct": false } ],
                   "feedbackCorrect": "Benar! ...", "feedbackWrong": "Kurang tepat. ..." } } ] }
```

- Parse `content` according to `kind`:
  - `READ` has `paragraphs`.
  - `EXAMPLES` has `examples[]` with `label`, `tone` (`GOOD`/`BAD`), `caption` and an optional `illustration`.
  - `QUIZ` has `question`, `options` (always 4, one with `correct: true`), `feedbackCorrect` and `feedbackWrong`.
- A `LESSON` is 1–2 READ/EXAMPLES steps, then one QUIZ. A `PRACTICE` level is 3 QUIZ steps.
- `illustration` keys: `CROSSING_GREEN`, `CROSSING_RED_CAR`. Draw these in Compose. For an unknown or missing key, show no picture.
- The answers are included, so grade the quiz in the app.
- Locked level → **403** `Selesaikan level sebelumnya dulu ya!` (same text as the snackbar). Unknown level → **404** `Level tidak ditemukan`. Completed levels can be replayed.

### POST /courses/{courseId}/levels/{levelId}/complete

Call this when the user finishes the level.

```json
{ "correct": true, "minutesSpent": 4 }
```

**200**:

```json
{ "course": { ...same shape as GET /courses/{id}, with the new states... },
  "progress": { ...same shape as GET /me/progress... } }
```

- `minutesSpent` is added to today's study minutes (clamped to 0–60).
- Use the response to update the course map and the home screen without extra requests.
- Locked level → **403**. Calling it again on a completed level is fine.

### POST /chat (not ready yet)

```json
{ "query": "Apakah penumpang motor wajib pakai helm?", "voice_mode": false }
```

Note: this body is **snake_case** (`voice_mode`), unlike the rest of the API.

The response is a **streamed `text/plain`** body (not JSON). Read it incrementally with OkHttp `response.body!!.source()` and append text as it arrives. Don't use `.string()`. `voice_mode: true` returns short plain-text answers suited to on-device TTS.

## Demo accounts

| Email | Password | State |
|---|---|---|
| `budi@legaloo.id` | `legaloo123` | Budi Santoso: course 1 levels 1–2 done (level 3 active), course 2 level 1 done, 7-day streak, 6/10 minutes today |
| `siti.rahma@gmail.com` | `hukum2026` | Siti Rahmawati: fresh account, no progress |

The backend team re-runs `db/seed.sql` on the morning of the demo, which resets both accounts. Any account registered while testing stays in the database.

## Quick test from a terminal

```sh
B=http://localhost:8000
T=$(curl -s -X POST $B/auth/login -H 'content-type: application/json' \
  -d '{"email":"budi@legaloo.id","password":"legaloo123"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s $B/courses -H "authorization: Bearer $T"
```
