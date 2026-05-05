"""Nihongo Mode Handler — completely isolated routing for Japanese teacher mode."""

import asyncio
import logging

from litellm import acompletion
from telegram import Update
from telegram.ext import ContextTypes

from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode
from skills.nihongo.quiz_engine import QuizEngine
from skills.nihongo.sensei_prompt import build_sensei_system_prompt
from skills.nihongo.vocab_tracker import VocabTracker
from skills.nihongo.voice_pipeline import (  # type: ignore[reportOptionalMemberAccess]
    text_to_speech_japanese,
    transcribe_voice_note,
)

logger = logging.getLogger("nihongo.handler")

NIHONGO_COMMANDS = {
    "/nihonko": "activate_default",
    "/nihonko chat": "activate_chat",
    "/nihonko voice": "activate_voice",
    "/nihonko quiz": "activate_quiz",
    "/nihonko story": "activate_story",
    "/nihonko free": "activate_free",
}


async def _call_llm(system_prompt: str, user_message: str, model: str = "claude-3-5-haiku") -> str:
    try:
        response = await acompletion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=800,
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"]  # type: ignore[reportIndexIssue]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return "Maaf, Sensei sedang trouble. Coba lagi ya!"


async def handle_nihongo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    text = update.message.text.strip().lower() if update.message.text else ""  # type: ignore[reportOptionalMemberAccess]
    user_id = update.effective_user.id  # type: ignore[reportOptionalMemberAccess]

    if text == "/nihonko" or text.startswith("/nihonko chat"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.CHAT)
        await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
            "⛩ *Nihongo Mode ON* | Chat Mode\n\n"
            "Halo Bashara! Sensei siap ngajarin kamu Bahasa Jepang.\n\n"
            "📖 Level: JLPT N5\n"
            "🎙 Voice: OFF (ketik /nihongo voice untuk aktifkan)\n"
            "🎓 Furigana + Romaji: ON\n\n"
            "Mau mulai dari mana?\n"
            "- /nihongo quiz — langsung drilling\n"
            "- /nihongo story — belajar lewat cerita\n"
            "- /nihongo free — ngobrol bebas\n"
            "- Atau langsung ketik aja topik yang mau dipelajari!",
            parse_mode="HTML",
        )
        return True

    elif text.startswith("/nihongo voice"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.CHAT)
        session.voice_enabled = True  # type: ignore[reportOptionalMemberAccess]
        await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
            "⛩ *Nihongo Mode ON* | Voice Mode\n\n"
            "🎙 Kirim voice note → Sensei transkripsi + koreksi + balas dengan suara.\n"
            "Kecepatan: SLOW (75%) — cocok untuk N5.\n"
            "TTS: VoiceVox (neural) atau gTTS jika VoiceVox tidak tersedia.\n\n"
            "Coba kirim voice note dalam Bahasa Jepang — apapun yang kamu bisa!",
            parse_mode="HTML",
        )
        return True

    elif text.startswith("/nihonko quiz"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.QUIZ)
        QuizEngine.reset_session(user_id)
        await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
            "⛩ *Nihongo Mode ON* | Quiz Mode\n\n"
            "🎯 Mulai drilling! Skor kamu: 0/0 | Streak: 0\n"
            "Level: N5 | Vocab flash cards + fill-in-the-blank\n\n"
            'Siap? Ketik "mulai" untuk soal pertama!',
            parse_mode="HTML",
        )
        return True

    elif text.startswith("/nihonko story"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.STORY)
        await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
            "⛩ *Nihongo Mode ON* | Story Mode\n\n"
            "📖 Mari kita belajar lewat cerita!\n"
            "Bashara adalah protagonis dalam petualangan bahasa Jepang.\n"
            "Setiap scene butuh jawaban dalam Bahasa Jepang untuk lanjut.\n\n"
            'Siap? Ketik "mulai" untuk mulai cerita!',
            parse_mode="HTML",
        )
        return True

    elif text.startswith("/nihonko free"):
        session = NihongoModeManager.activate(user_id, NihongoSubMode.FREE)
        await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
            "⛩ *Nihongo Mode ON* | Free Chat Mode\n\n"
            "🗣 Ngobrol bebas dalam Bahasa Jepang!\n"
            "Sensei akan perbaiki kesalahanmu di akhir response.\n"
            "Tidak ada struktur lesson — santai aja!\n\n"
            "Mau bicara tentang apa?",
            parse_mode="HTML",
        )
        return True

    elif text in ["/stopp", "/stop", "/nihongo_off"]:
        NihongoModeManager.deactivate(user_id)
        await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
            "⛩ Nihongo Mode *OFF*.\n\n"
            "Legion kembali ke mode normal. またね！ (Mata ne! = Sampai jumpa!)\n"
            "Progress kamu tersimpan. Ketik /nihongo kapanpun untuk lanjut.",
            parse_mode="HTML",
        )
        return True

    elif text == "/nihonko status":
        session = NihongoModeManager.get_session(user_id)
        score = QuizEngine.get_user_score(user_id)

        # Try to include new component stats if available
        srs_mastery = None
        _ = None  # bloom_dist reserved for future
        _ = None  # phoneme_weak reserved for future

        try:
            from skills.nihongo.mastery_gate import MasteryGate
            from skills.nihongo.srs_engine import SRSEngine

            srs = SRSEngine()
            srs_mastery = srs.get_mastery_percentage(user_id)

            _ = MasteryGate()  # reserved for future complexity scoring
        except Exception:
            pass  # Gracefully degrade if components not available

        # Build dashboard
        words_mastered = len(session.words_mastered)
        words_total = 120  # Approximate N5 total
        words_pct = (words_mastered / words_total) * 100 if words_total > 0 else 0

        grammar_total = 15
        grammar_pct = min(100, (len(session.grammar_seen) / grammar_total) * 100)

        srs_display = f"{srs_mastery:.1f}%" if srs_mastery is not None else "N/A"

        # Build progress bar
        def progress_bar(pct: float, length: int = 8) -> str:
            filled = int(pct / (100 / length))
            return "█" * filled + "░" * (length - filled)

        dashboard = f"""
╔══════════════════════════════════════════════╗
║  ⛩ NIHONGO MODE — 日本語학습                  ║
║  Hanako Sensei | Status: {"Active✅" if session.active else "Inactive❌"}         ║
╠══════════════════════════════════════════════╣
║  📊 Progress                                 ║
║  Words Mastered: {words_mastered}/{words_total}  [{progress_bar(words_pct)}] {words_pct:.1f}%║
║  Grammar Points: {len(session.grammar_seen)}/{grammar_total}    [{progress_bar(grammar_pct)}] {grammar_pct:.0f}%   ║
║  SRS Mastery:     {srs_display}                       ║
╠══════════════════════════════════════════════╣
║  🎯 Quiz Stats                              ║
║  Score: {score["correct"]}/{score["total"]} | Streak: {score["streak"]} 🔥                ║
╠══════════════════════════════════════════════╣
║  📅 Next Review                             ║
║  Mode: {session.sub_mode.value.upper():6} | Level: {session.jlpt_level} | Exchanges: {session.exchange_count}    ║
╚══════════════════════════════════════════════╝
"""
        await update.message.reply_text(dashboard, parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    elif text.startswith("/nihonko level"):
        level = text.replace("/nihonko level", "").strip()
        if level in ["n5", "n4", "n3"]:
            NihongoModeManager.set_level(user_id, level.upper())
            await update.message.reply_text(  # type: ignore[reportOptionalMemberAccess]
                f"⛩ Level changed to *JLPT {level.upper()}*\n\n"
                f"Mode难度: {'Pemula' if level.upper() == 'N5' else 'Menengah' if level.upper() == 'N4' else 'Lanjutan'}",
                parse_mode="HTML",
            )
            return True

    elif text == "/furigana on":
        session = NihongoModeManager.get_session(user_id)
        session.show_furigana = True
        await update.message.reply_text("⛩ Furigana: *ON* ✅", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    elif text == "/furigana off":
        session = NihongoModeManager.get_session(user_id)
        session.show_furigana = False
        await update.message.reply_text("⛩ Furigana: *OFF*", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    elif text == "/romaji on":
        session = NihongoModeManager.get_session(user_id)
        session.show_romaji = True
        await update.message.reply_text("⛩ Romaji: *ON* ✅", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    elif text == "/romaji off":
        session = NihongoModeManager.get_session(user_id)
        session.show_romaji = False
        await update.message.reply_text("⛩ Romaji: *OFF*", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    elif text == "/slow on":
        session = NihongoModeManager.get_session(user_id)
        session.slow_speech = True
        await update.message.reply_text("⛩ TTS Speed: *SLOW (75%)*", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    elif text == "/slow off":
        session = NihongoModeManager.get_session(user_id)
        session.slow_speech = False
        await update.message.reply_text("⛩ TTS Speed: *Normal*", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        return True

    return False


async def handle_nihongo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id  # type: ignore[reportOptionalMemberAccess]
    session = NihongoModeManager.get_session(user_id)

    if update.message.voice:  # type: ignore[reportOptionalMemberAccess]
        await _handle_voice_input(update, context, session)
        return

    user_text = update.message.text or ""  # type: ignore[reportOptionalMemberAccess]

    exchange_num = NihongoModeManager.increment_exchange(user_id)

    system_prompt = build_sensei_system_prompt(session)

    if exchange_num % 3 == 0 and session.sub_mode != NihongoSubMode.QUIZ:
        system_prompt += "\n\nFORCED: End this response with a mini-quiz question."

    response_text = await _call_llm(system_prompt, user_text)

    await update.message.reply_text(response_text, parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]

    if session.voice_enabled:  # type: ignore[reportOptionalMemberAccess]
        audio_bytes = await text_to_speech_japanese(response_text, slow_speech=session.slow_speech)
        if audio_bytes:
            await update.message.reply_voice(voice=audio_bytes)  # type: ignore[reportOptionalMemberAccess]

    task = asyncio.create_task(VocabTracker.track_from_response(user_id, response_text))
    task.add_done_callback(
        lambda t: t.result() if not t.cancelled() and t.exception() is None
        else logger.warning("VocabTracker.track_from_response failed: %s", t.exception())
    )


async def _handle_voice_input(update: Update, context: ContextTypes.DEFAULT_TYPE, session) -> None:
    voice_file = await update.message.voice.get_file()  # type: ignore[reportOptionalMemberAccess]
    voice_bytes = await voice_file.download_as_bytearray()

    processing_msg = await update.message.reply_text("🎙 Transkripsi...")  # type: ignore[reportOptionalMemberAccess]

    transcription = await transcribe_voice_note(bytes(voice_bytes), language="ja")

    await processing_msg.edit_text(
        f"🎙 *Kamu bilang:* {transcription}\n\n🤔 Sensei sedang memproses...",
        parse_mode="HTML",
    )

    NihongoModeManager.increment_exchange(session.user_id)
    system_prompt = build_sensei_system_prompt(session)
    system_prompt += f"\n\nBashara sent a voice note. Transcription: '{transcription}'. Evaluate his Japanese pronunciation attempt and continue the lesson."

    response_text = await _call_llm(system_prompt, f"[Voice input transcribed]: {transcription}")

    await update.message.reply_text(response_text, parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]

    audio_bytes = await text_to_speech_japanese(response_text, slow_speech=session.slow_speech)
    if audio_bytes:
        await update.message.reply_voice(voice=audio_bytes)  # type: ignore[reportOptionalMemberAccess]
