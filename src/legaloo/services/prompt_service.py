"""Prompt assembly. Keep the voice-mode rules mechanical and short."""

from ..core.config import get_settings
from ..schemas.document import Chunk

_VOICE_RULES = """\
Jawab dalam Bahasa Indonesia.
- Maksimal 2 kalimat.
- Teks biasa saja. Tanpa daftar, tanpa tanda bintang, tanpa emoji.
- Tulis angka dengan huruf.
- Kalau konteks tidak memuat jawabannya, bilang tidak tahu."""

_TEXT_RULES = """\
Jawab dalam Bahasa Indonesia, berdasarkan konteks di bawah.
Sebutkan sumbernya. Kalau konteks tidak memuat jawabannya, bilang tidak tahu."""

# No retrieved context: answer from general knowledge instead of refusing.
# chat_service prepends a fixed "informasi umum" note, so the model doesn't add one.
_VOICE_RULES_GENERAL = """\
Jawab dalam Bahasa Indonesia, untuk pelajar muda, dengan bahasa sederhana.
- Maksimal 2 kalimat.
- Teks biasa saja. Tanpa daftar, tanpa tanda bintang, tanpa emoji.
- Tulis angka dengan huruf.
- Kalau tidak yakin, sarankan bertanya ke guru atau orang tua."""

_TEXT_RULES_GENERAL = """\
Jawab dalam Bahasa Indonesia, untuk pelajar muda, dengan bahasa sederhana dan ramah.
Jawab singkat berdasarkan pengetahuan umum tentang hukum Indonesia.
Jangan mengarang nomor pasal. Kalau tidak yakin, sarankan bertanya ke guru atau orang tua."""


def build_prompt(query: str, chunks: list[Chunk], voice_mode: bool) -> str:
    s = get_settings()

    context, used = [], 0
    for c in chunks:
        block = f"[{c.source}]\n{c.content}"
        if used + len(block) > s.max_context_chars:
            break
        context.append(block)
        used += len(block)

    if context:
        rules = _VOICE_RULES if voice_mode else _TEXT_RULES
    else:
        rules = _VOICE_RULES_GENERAL if voice_mode else _TEXT_RULES_GENERAL
    joined = "\n\n".join(context) if context else "(tidak ada konteks)"

    # Rules are restated after the context: small models lose instructions
    # that sit far from the user turn.
    return (
        f"{rules}\n\n"
        f"KONTEKS:\n{joined}\n\n"
        f"PERTANYAAN: {query}\n\n"
        f"Ingat: {rules}\n\nJAWABAN:"
    )
