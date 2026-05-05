"""CulturalIntel — Cultural Intelligence Layer for Nihongo Mode.

Provides context-aware cultural guidance for Japanese language learning.
Integrates cultural intelligence into lessons without breaking the flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ImportanceLevel(Enum):
    """Importance level for cultural notes."""

    HIGH = "high"  # Critical for daily life/social
    MEDIUM = "medium"  # Good to know
    LOW = "low"  # Nice to know


@dataclass
class CulturalNote:
    """A cultural note with Japanese practice and explanation.

    Attributes:
        topic: The cultural topic (e.g., "bowing", "keigo")
        japanese_practice: What Japanese people actually do/say
        indonesian_explanation: Explanation in Indonesian
        importance_level: How critical this is for learners
    """

    topic: str
    japanese_practice: str
    indonesian_explanation: str
    importance_level: ImportanceLevel


class CulturalIntel:
    """Cultural Intelligence for Nihongo Mode.

    Provides context-aware cultural guidance covering bowing, business
    card exchange, keigo levels, gift-giving, seasonal greetings,
    and university etiquette.
    """

    # Keigo levels guide
    KEIGO_GUIDANCE = {
        "N5": """Keigo untuk level N5 — fokus pada dasar:
- ます-form (masu-form) sudah cukup sopan untuk sebagian besar situasi
- 先生 (sensei) selalu gunakan untuk guru/dosen
- ください (kudasai) untuk permintaan sopan
- ありがとうございます (arigatou gozaimasu) untuk terima kasih formal
- すみません (sumimasen) untuk minta maaf ringan dan perhatian
- Tidak perlu terlalu khawatir tentang keigo tinggi (丁寧語 sudah cukup)
""",
        "N4": """Keigo level N4 — mulai kenal尊敬語 (sonkeigo) dan 丁重語 (teineigo):
- ，先生 (sensei) 加減 (kanso) sudah bisa dipakai
- お/~になります (o/~ ni narimasu) untuk尊敬語 dasar
- ございます (gozaimasu) untuk bentuk sangat sopan
- Mulai perlu 注意する (chuui suru) perbedaan 丁寧語 dan 尊敬語
""",
        "N3+": """Keigo level N3+ — harus kuasai尊敬語 (sonkeigo) dan 谦遜語 (kensongo):
- お/~になります (o/~ ni narimasu) vs お/~します (o/~ shimasu)
- いたします (itashimasu) untuk谦虚 (sopan rendah diri)
- 差し上げます (sashiagemasu) untuk "give" dalam尊敬語
- 頂戴いたします (choudai itashimasu) untuk "receive" dengan sangat sopan
- 承知いたしました (shouchi itashimashita) untuk "I understand" formal
""",
    }

    # Cultural notes database
    CULTURAL_NOTES = {
        "bowing": [
            CulturalNote(
                topic="bowing",
                japanese_practice="お辞儀 (ojigi) — depth varies by context: 15° casual greeting, 30° respect, 45° deep apology",
                indonesian_explanation="Bowing di Jepang menunjukkan rasa hormat. Sudut membungkuk tergantung seberapa hormat kamu ingin tunjukkan. Untuk mahasiswa, 15-30° sudah cukup untuk daily interaction.",
                importance_level=ImportanceLevel.HIGH,
            ),
            CulturalNote(
                topic="bowing",
                japanese_practice="In business, exchange business cards with both hands while bowing slightly",
                indonesian_explanation="Di Jepang, 名刺 (meishi/business card) sangat penting. Selaluserahkan dengan kedua tangan dan baca sebentar sebelum menyimpan. Ini menunjukkan rasa hormat.",
                importance_level=ImportanceLevel.HIGH,
            ),
        ],
        "meishi": [
            CulturalNote(
                topic="business_card-exchange",
                japanese_practice="名片のやり取り:両手で差し出し、名刺を受け取った後、一瞬読んでから丁寧にしまってください",
                indonesian_explanation="Di Jepang, 名刺 (meishi) adalah identitas profesional. Jangan langsung simpan tanpa membaca. Jangan tulis apapun di 名刺 — itu dianggap tidak sopan.",
                importance_level=ImportanceLevel.HIGH,
            ),
            CulturalNote(
                topic="business-card-exchange",
                japanese_practice="Receive with right hand, place on left palm while reading",
                indonesian_explanation="Saat terima 名刺, gunakan tangan kanan untuk ambil, letakkan di telapak kiri sambil membaca. Ini gesture yang menunjukkan kamu menghargai orang tersebut.",
                importance_level=ImportanceLevel.HIGH,
            ),
        ],
        "keigo": [
            CulturalNote(
                topic="keigo-levels",
                japanese_practice="丁寧語 (teineigo) → 尊敬語 (sonkeigo) → 谦逊語 (kensongo)",
                indonesian_explanation="Jepang punya 3 level kesopanan: 丁寧語 untuk sehari-hari, 尊敬語 untuk menghormati orang lain, 谦逊語 untuk merendahkan diri sendiri. Menggunakan keigo yang tepat sangat penting di lingkungan profesional.",
                importance_level=ImportanceLevel.HIGH,
            ),
            CulturalNote(
                topic="keigo",
                japanese_practice="ません (masen) vs ありません (arimasen) —后者 lebih formal",
                indonesian_explanation="Bentuk ありません adalah versi lebih sopan dari ません. Gunakan di situasi formal seperti Presentasi, bisnis, atau dengan professor.",
                importance_level=ImportanceLevel.MEDIUM,
            ),
        ],
        "gift-giving": [
            CulturalNote(
                topic="gift-giving",
                japanese_practice="お土産 (omiyage) — Souvenir dari tempat travel untuk rekan kerja/keluarga",
                indonesian_explanation="Di Jepang, kebiasaan memberi お土産 (omiyage/souvenir) sangat lazim. Saattravel, bawalah oleh-oleh kecil untuk rekan kerja. Tradition ini называется 'omiyage'.",
                importance_level=ImportanceLevel.MEDIUM,
            ),
            CulturalNote(
                topic="gift-giving",
                japanese_practice="Wrap with yopic paper and give with both hands",
                indonesian_explanation="Pemberian hadiah di Jepang biasanya dibungkus rapi. Gunakan kertas regalo (yopic paper) dan berikan dengan kedua tangan. Jangan gunakan angka 4 dan 9 sebagai quantity — mereka dianggap tidak beruntung.",
                importance_level=ImportanceLevel.LOW,
            ),
        ],
        "seasonal": [
            CulturalNote(
                topic="seasonal-greetings",
                japanese_practice="あけましておめでとう (akemashite omedetou) — Happy New Year",
                indonesian_explanation="Di Jepang, tahun baru adalah holiday paling penting. Ucapan umum adalah あけましておめでとうございます yang biasanya disingkat menjadi 明けまして atau 今年もよろしく.",
                importance_level=ImportanceLevel.HIGH,
            ),
            CulturalNote(
                topic="seasonal-greetings",
                japanese_practice="お盆 (obon) — Mid-August ancestor worship period",
                indonesian_explanation="お盆 adalah waktu untuk menghormati leluhur, biasanya pertengahan Agustus. Banyak orang回到家乡 (modoru furusato/kembali ke kampung halaman). Jika Jepang之旅 (tabi) saat ini, tetap hati-hati dengan transportasi.",
                importance_level=ImportanceLevel.MEDIUM,
            ),
        ],
        "university": [
            CulturalNote(
                topic="university-etiquette",
                japanese_practice="研究室訪問:アポイントメントが必要です。メールか直接 약속 (yakusoku)を取る",
                indonesian_explanation="Di Jepang, datang ke 研究室 (laboratorium/tempat professor) tanpa appointments (チムチ/hole) dianggap tidak sopan. Selalu buat janji dulu melalui email atau saat kelas.",
                importance_level=ImportanceLevel.HIGH,
            ),
            CulturalNote(
                topic="university-etiquette",
                japanese_practice="研究室では 先生 (sensei) の時間を尊重してください。短く効率的に",
                indonesian_explanation="Jika sudah dapatappointment dengan professor, datang tepat waktu dan prepare questions sebelumnya. Professor Jepang biasanya sangat sibuk, jadi menghargai waktu mereka adalah KEISOKU (kesopanan dasar).",
                importance_level=ImportanceLevel.HIGH,
            ),
        ],
    }

    def get_cultural_notes_for_topic(self, topic: str) -> list[CulturalNote]:
        """Get cultural notes for a specific topic.

        Args:
            topic: The topic identifier (e.g., "bowing", "keigo")

        Returns:
            List of CulturalNote objects for that topic
        """
        return self.CULTURAL_NOTES.get(topic, [])

    def get_keigo_awareness(self, user_level: str) -> str:
        """Get keigo guidance for the user's JLPT level.

        Args:
            user_level: JLPT level (N5, N4, N3, etc.)

        Returns:
            String with keigo guidance for that level
        """
        level_key = user_level.upper().replace("JLPT", "").strip()
        return self.KEIGO_GUIDANCE.get(level_key, self.KEIGO_GUIDANCE.get("N5", ""))

    def get_situation_culture(self, location: str, situation: str) -> CulturalNote | None:
        """Get cultural note for a specific location and situation.

        Args:
            location: Location context (e.g., "university", "business")
            situation: Situation within that location (e.g., "meeting_professor")

        Returns:
            CulturalNote or None if not found
        """
        # Map location/situation to topic
        mapping = {
            ("university", "meeting_professor"): "university-etiquette",
            ("university", "class"): "university-etiquette",
            ("business", "exchange"): "business-card-exchange",
            ("daily", "bowing"): "bowing",
            ("daily", "greeting"): "bowing",
        }

        topic = mapping.get((location.lower(), situation.lower()))
        if topic:
            notes = self.get_cultural_notes_for_topic(topic)
            if notes:
                return notes[0]

        # Fallback search through all notes
        for notes in self.CULTURAL_NOTES.values():
            for note in notes:
                if location.lower() in note.topic or situation.lower() in note.topic:
                    return note

        return None

    def format_cultural_note(self, note: CulturalNote) -> str:
        """Format a cultural note for Telegram output.

        Args:
            note: The CulturalNote to format

        Returns:
            Telegram-formatted string with HTML
        """
        importance_emoji = {
            ImportanceLevel.HIGH: "🔴",
            ImportanceLevel.MEDIUM: "🟡",
            ImportanceLevel.LOW: "⚪",
        }

        emoji = importance_emoji.get(note.importance_level, "⚪")

        return f"""
🏯 <b>Cultural Note:</b> {note.topic.capitalize()} {emoji}

📝 <b>Japanese Practice:</b>
{note.japanese_practice}

🇮🇩 <b>Penjelasan:</b>
{note.indonesian_explanation}

💡 <b>Importance:</b> {note.importance_level.value.upper()}
"""
