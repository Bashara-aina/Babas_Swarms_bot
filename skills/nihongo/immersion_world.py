"""ImmersionWorld — Narita-Specific Japanese Scenarios.

Provides location-specific Japanese scenarios for contextual learning.
Scenarios are set in real locations Bashara encounters daily.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Location(Enum):
    """Location contexts for immersion scenarios."""

    NARITA_AIRPORT = "narita_airport"
    KEIO_SHIBAURA_CAMPUS = "keio_shibaura_campus"
    CONBINI = "conbini"
    TRAIN_STATION = "train_station"
    HOSPITAL = "hospital"
    CITY_HALL = "city_hall"


@dataclass
class Scenario:
    """A location-specific scenario for immersive learning."""

    title: str
    location: Location
    situation: str
    dialogue: list[dict[str, str]]  # [{"speaker": "person_a", "japanese": "...", "meaning": "..."}]
    vocab: list[dict[str, str]]  # [{"word": "...", "reading": "...", "meaning": "..."}]
    cultural_notes: list[str]


class ImmersionWorld:
    """Location-aware immersion scenarios for Nihongo Mode.

    Generates rich, contextual Japanese scenarios based on real locations
    in Narita that Bashara encounters daily.
    """

    # Narita-specific vocabulary
    NARITA_VOCAB = [
        {"word": "成田空港", "reading": "なりたくうこう", "meaning": "Narita Airport", "category": "place"},
        {"word": "エバー航空", "reading": "エバーこうくう", "meaning": "Eva Air", "category": "brand"},
        {"word": "京成線", "reading": "けいせいせん", "meaning": "Keisei Line", "category": "transport"},
        {"word": "第１ターミナル", "reading": "だい1ターミナル", "meaning": "Terminal 1", "category": "place"},
        {"word": "第２ターミナル", "reading": "だい2ターミナル", "meaning": "Terminal 2", "category": "place"},
        {"word": "バス", "reading": "バス", "meaning": "bus", "category": "transport"},
        {"word": "モノレール", "reading": "モノレール", "meaning": "monorail", "category": "transport"},
        {"word": "出口", "reading": "でぐち", "meaning": "exit", "category": "place"},
        {"word": "入口", "reading": "いりぐち", "meaning": "entrance", "category": "place"},
        {"word": "電車", "reading": "でんしゃ", "meaning": "train", "category": "transport"},
        {"word": "切符", "reading": "きっぷ", "meaning": "ticket", "category": "transport"},
        {"word": "改札口", "reading": "かいさつぐち", "meaning": "ticket gate", "category": "place"},
        {"word": "地図", "reading": "ちず", "meaning": "map", "category": "tech"},
    ]

    # Campus-specific vocabulary
    CAMPUS_VOCAB = [
        {"word": "大学", "reading": "だいがく", "meaning": "university", "category": "place"},
        {"word": "研究室", "reading": "けんきゅうしつ", "meaning": "professor's office/lab", "category": "place"},
        {"word": "教官室", "reading": "きょうかんしつ", "meaning": "faculty room", "category": "place"},
        {"word": "図書館", "reading": "としょかん", "meaning": "library", "category": "place"},
        {"word": "食堂", "reading": "しょくどう", "meaning": "cafeteria", "category": "place"},
        {"word": "学生課", "reading": "がくせいか", "meaning": "student affairs office", "category": "place"},
        {"word": "論文", "reading": "ろんぶん", "meaning": "thesis/paper", "category": "academic"},
        {"word": "発表", "reading": "はっぴょう", "meaning": "presentation", "category": "academic"},
        {"word": "実験", "reading": "じっけん", "meaning": "experiment", "category": "academic"},
        {"word": "データ", "reading": "データ", "meaning": "data", "category": "academic"},
    ]

    # Conbini vocabulary
    CONBINI_VOCAB = [
        {"word": "お弁当", "reading": "おべんとう", "meaning": "boxed lunch/bento", "category": "food"},
        {"word": "おにぎり", "reading": "おにぎり", "meaning": "rice ball", "category": "food"},
        {"word": "サンドイッチ", "reading": "サンドイッチ", "meaning": "sandwich", "category": "food"},
        {"word": "飲み物", "reading": "のみもの", "meaning": "drink", "category": "food"},
        {"word": "お茶", "reading": "おちゃ", "meaning": "tea/green tea", "category": "food"},
        {"word": "コーヒー", "reading": "コーヒー", "meaning": "coffee", "category": "food"},
        {"word": "お会計", "reading": "おかいけい", "meaning": "checkout/total", "category": "service"},
        {"word": "塑料袋", "reading": "塑料袋", "meaning": "plastic bag", "category": "service"},
        {"word": "温める", "reading": "あたためる", "meaning": "to heat up", "category": "service"},
        {"word": "払い戻し", "reading": "はらいもどし", "meaning": "refund", "category": "service"},
    ]

    SCENARIOS = {
        Location.NARITA_AIRPORT: {
            "check_in": Scenario(
                title="、成田空港チェックイン",
                location=Location.NARITA_AIRPORT,
                situation="Checking in at Narita Airport",
                dialogue=[
                    {
                        "speaker": "カウンター",
                        "japanese": "パスポートを見せてください。",
                        "romaji": "pasupooto wo misete kudasai",
                        "meaning": "Please show me your passport.",
                    },
                    {
                        "speaker": "あなた",
                        "japanese": "はい、どうぞ。",
                        "romaji": "hai, douzo",
                        "meaning": "Here you go.",
                    },
                    {
                        "speaker": "カウンター",
                        "japanese": "スーツケースは預けますか？",
                        "romaji": "suutsukeesu wa azukemasu ka",
                        "meaning": "Will you check your suitcase?",
                    },
                    {
                        "speaker": "あなた",
                        "japanese": "はい、お願いします。",
                        "romaji": "hai, onegaishimasu",
                        "meaning": "Yes, please.",
                    },
                    {
                        "speaker": "カウンター",
                        "japanese": "窗口は23Aです。",
                        "romaji": "madoguchi wa 23A desu",
                        "meaning": "Your gate is 23A.",
                    },
                ],
                vocab=[
                    {"word": "チェックイン", "reading": "チェックイン", "meaning": "check-in", "category": "travel"},
                    {"word": "パスポート", "reading": "パスポート", "meaning": "passport", "category": "travel"},
                    {"word": "スーツケース", "reading": "スーツケース", "meaning": "suitcase", "category": "travel"},
                    {"word": "預ける", "reading": "あずける", "meaning": "to check (baggage)", "category": "verb"},
                    {"word": "窓口", "reading": "まどぐち", "meaning": "window/counter", "category": "place"},
                ],
                cultural_notes=[
                    "Japanese airport staff use polite keigo — respond with ます form",
                    "Always keep your boarding pass handy after check-in",
                ],
            ),
            "asking_directions": Scenario(
                title="成田空港で道を聞く",
                location=Location.NARITA_AIRPORT,
                situation="Asking for directions at Narita Airport",
                dialogue=[
                    {
                        "speaker": "あなた",
                        "japanese": "すみません、出口はどこですか？",
                        "romaji": "sumimasen, deguchi wa doko desu ka",
                        "meaning": "Excuse me, where is the exit?",
                    },
                    {
                        "speaker": "人",
                        "japanese": "あのう、左側のエスカレーターを降りてください。",
                        "romaji": "anou, hidari gawa no esukareetaa wo orite kudasai",
                        "meaning": "Please go down the escalator on the left.",
                    },
                    {
                        "speaker": "あなた",
                        "japanese": "ありがとうございます。",
                        "romaji": "arigatou gozaimasu",
                        "meaning": "Thank you very much.",
                    },
                ],
                vocab=[
                    {"word": "出口", "reading": "でぐち", "meaning": "exit", "category": "place"},
                    {
                        "word": "エスカレーター",
                        "reading": "エスカレーター",
                        "meaning": "escalator",
                        "category": "place",
                    },
                    {"word": "左側", "reading": "ひだりがわ", "meaning": "left side", "category": "direction"},
                    {"word": "右側", "reading": "みぎがわ", "meaning": "right side", "category": "direction"},
                ],
                cultural_notes=[
                    "Always start with すみません (excuse me) when asking for help",
                    "Bow slightly when thanking someone",
                ],
            ),
        },
        Location.KEIO_SHIBAURA_CAMPUS: {
            "meeting_professor": Scenario(
                title="研究室で教授と会う",
                location=Location.KEIO_SHIBAURA_CAMPUS,
                situation="Meeting with professor at campus",
                dialogue=[
                    {
                        "speaker": "あなた",
                        "japanese": "すみません、山田先生はいらっしゃいますか？",
                        "romaji": "sumimasen, Yamada-sensei wa irasshaimasu ka",
                        "meaning": "Excuse me, is Professor Yamada in?",
                    },
                    {
                        "speaker": " секретар",
                        "japanese": "はい、お待ちください。",
                        "romaji": "hai, omachi kudasai",
                        "meaning": "Yes, please wait.",
                    },
                    {
                        "speaker": "教授",
                        "japanese": "的山です。 어떡好啊？",
                        "romaji": "Yamada desu. Dou itashimashite",
                        "meaning": "I'm Yamada. How can I help you?",
                    },
                    {
                        "speaker": "あなた",
                        "japanese": "はじめまして、Basharaです，宜しくお願いします。",
                        "romaji": "hajimemashite, Bashara desu, yoroshiku onegaishimasu",
                        "meaning": "Nice to meet you, I'm Bashara, pleased to meet you.",
                    },
                ],
                vocab=[
                    {"word": " 教授", "reading": "きょうじゅ", "meaning": "professor", "category": "academic"},
                    {
                        "word": " 研究室",
                        "reading": "けんきゅうしつ",
                        "meaning": "professor's office/lab",
                        "category": "place",
                    },
                    {"word": " 先生", "reading": "せんせい", "meaning": "teacher/master", "category": "academic"},
                    {
                        "word": " ，宜しく",
                        "reading": "yoroshiku",
                        "meaning": "please (treat me well)",
                        "category": "expression",
                    },
                ],
                cultural_notes=[
                    "Always use 先生 (sensei) when addressing professors",
                    "Bow when greeting and when leaving",
                    "始めるまして is used when meeting someone for the first time",
                ],
            ),
            "campus_directions": Scenario(
                title=" campusで道を聞く",
                location=Location.KEIO_SHIBAURA_CAMPUS,
                situation="Asking for directions on campus",
                dialogue=[
                    {
                        "speaker": "あなた",
                        "japanese": "すみません、図書館はどこですか？",
                        "romaji": "sumimasen, toshokan wa doko desu ka",
                        "meaning": "Excuse me, where is the library?",
                    },
                    {
                        "speaker": "学生",
                        "japanese": "このビルの奥の階段を上がってください。",
                        "romaji": "kono biru no oku no kaidan wo agatte kudasai",
                        "meaning": "Please go up the stairs at the back of this building.",
                    },
                    {
                        "speaker": "あなた",
                        "japanese": "ありがとうございます。",
                        "romaji": "arigatou gozaimasu",
                        "meaning": "Thank you.",
                    },
                ],
                vocab=[
                    {"word": "建物", "reading": "ビル/たてもの", "meaning": "building", "category": "place"},
                    {"word": "階段", "reading": "かいたん", "meaning": "stairs/steps", "category": "place"},
                    {"word": "图书馆", "reading": "としょかん", "meaning": "library", "category": "place"},
                    {"word": "奥", "reading": "おく", "meaning": "inside/back", "category": "direction"},
                ],
                cultural_notes=[
                    " 大学 students are generally helpful — don't hesitate to ask",
                    "Use この (kono) to point to nearby things",
                ],
            ),
        },
        Location.CONBINI: {
            "buying_bento": Scenario(
                title="コンビニでお弁当を買う",
                location=Location.CONBINI,
                situation="Buying bento at a conbini",
                dialogue=[
                    {
                        "speaker": "あなた",
                        "japanese": "お弁当 하나とコーヒー、おいくらですか？",
                        "romaji": "obentou to koohii, oikura desu ka",
                        "meaning": "How much is the bento and coffee?",
                    },
                    {
                        "speaker": "店员",
                        "japanese": "お会計は一、二、五、六円です。",
                        "romaji": "okaikei wa 1256en desu",
                        "meaning": "The total is 1256 yen.",
                    },
                    {
                        "speaker": "あなた",
                        "japanese": "カードで払えますか？",
                        "romaji": "kaado de haraemasu ka",
                        "meaning": "Can I pay by card?",
                    },
                    {
                        "speaker": "店员",
                        "japanese": "はい、もちろんです。",
                        "romaji": "hai, mochiron desu",
                        "meaning": "Yes, of course.",
                    },
                ],
                vocab=[
                    {"word": "お会計", "reading": "おかいけい", "meaning": "total/checkout", "category": "service"},
                    {"word": "お弁当", "reading": "おべんとう", "meaning": "bento/lunch box", "category": "food"},
                    {"word": "払う", "reading": "はらう", "meaning": "to pay", "category": "verb"},
                    {"word": "カード", "reading": "カード", "meaning": "card", "category": "service"},
                    {"word": "現金", "reading": "げんきん", "meaning": "cash", "category": "service"},
                ],
                cultural_notes=[
                    "Conbini staff are trained to be efficient — brief polite exchanges are normal",
                    "Say お会計是多少 before giving money",
                    " большинство conbinis accept card and cash",
                ],
            ),
            "microwave_request": Scenario(
                title="コンビニで Microwave を頼む",
                location=Location.CONBINI,
                situation="Asking to have food heated",
                dialogue=[
                    {
                        "speaker": "あなた",
                        "japanese": "すみません、これを温めてください。",
                        "romaji": "sumimasen, kore wo atatamete kudasai",
                        "meaning": "Excuse me, please heat this up.",
                    },
                    {
                        "speaker": "店员",
                        "japanese": "はいわかりました。少々お待ちください。",
                        "romaji": "hai, wakamarimashita. shoushou omachi kudasai",
                        "meaning": "OK, please wait a moment.",
                    },
                ],
                vocab=[
                    {"word": "温める", "reading": "あたためる", "meaning": "to heat up", "category": "verb"},
                    {"word": "少々", "reading": "しょうしょう", "meaning": "a little/short time", "category": "time"},
                    {
                        "word": "わかりました",
                        "reading": "わかりました",
                        "meaning": "I understand",
                        "category": "response",
                    },
                ],
                cultural_notes=[
                    "Use これこれを (kore wo) when pointing to something",
                    "Staff will usually heat it up behind the counter",
                ],
            ),
        },
    }

    def generate_scenario(self, location: Location, context: dict) -> Scenario:
        """Generate a scenario for a given location and situation.

        Args:
            location: The Location enum value
            context: Dict with 'situation' key for specific scenario variant

        Returns:
            Scenario object with dialogue, vocab, and cultural notes
        """
        situation = context.get("situation", "default")

        if location in self.SCENARIOS and situation in self.SCENARIOS[location]:
            return self.SCENARIOS[location][situation]

        # Return default scenario if not found
        return Scenario(
            title=f"Generic {location.value} scenario",
            location=location,
            situation=situation,
            dialogue=[],
            vocab=[],
            cultural_notes=["Practice this location's vocabulary in context."],
        )

    def get_narita_vocab(self) -> list[dict[str, str]]:
        """Get Narita-specific vocabulary list.

        Returns:
            List of vocabulary dicts for airport and transit
        """
        return self.NARITA_VOCAB.copy()

    def get_campus_phrases(self) -> list[dict[str, str]]:
        """Get university-specific Japanese phrases.

        Returns:
            List of phrase dicts for campus life
        """
        return self.CAMPUS_VOCAB.copy()

    def get_conbini_phrases(self) -> list[dict[str, str]]:
        """Get conbini-specific phrases.

        Returns:
            List of phrase dicts for convenience store interactions
        """
        return self.CONBINI_VOCAB.copy()

    def get_all_locations(self) -> list[Location]:
        """Get all available location enums."""
        return list(Location)

    def get_scenarios_for_location(self, location: Location) -> list[Scenario]:
        """Get all scenarios available for a location."""
        if location not in self.SCENARIOS:
            return []
        return list(self.SCENARIOS[location].values())
