"""Constants for Nihongo Mode — N5 vocab list, grammar patterns, lesson types."""

from enum import Enum


class LessonType(Enum):
    VOCAB = "vocab"
    GRAMMAR = "grammar"
    CONVERSATION = "conversation"
    QUIZ = "quiz"
    REVIEW = "review"


N5_VOCAB_SAMPLE = [
    {"word": "学生", "reading": "がくせい", "romaji": "gakusei", "meaning": "mahasiswa", "category": "people"},
    {"word": "先生", "reading": "せんせい", "romaji": "sensei", "meaning": "guru/dosen", "category": "people"},
    {"word": "大学", "reading": "だいがく", "romaji": "daigaku", "meaning": "universitas", "category": "place"},
    {"word": "日本語", "reading": "にほんご", "romaji": "nihongo", "meaning": "bahasa Jepang", "category": "language"},
    {"word": "食べる", "reading": "たべる", "romaji": "taberu", "meaning": "makan", "category": "verb"},
    {"word": "飲む", "reading": "のむ", "romaji": "nomu", "meaning": "minum", "category": "verb"},
    {"word": "行く", "reading": "いく", "romaji": "iku", "meaning": "pergi", "category": "verb"},
    {"word": "来る", "reading": "くる", "romaji": "kuru", "meaning": "datang", "category": "verb"},
    {"word": "見る", "reading": "みる", "romaji": "miru", "meaning": "melihat", "category": "verb"},
    {"word": "買う", "reading": "かう", "romaji": "kau", "meaning": "membeli", "category": "verb"},
    {"word": "書く", "reading": "かく", "romaji": "kaku", "meaning": "menulis", "category": "verb"},
    {"word": "読む", "reading": "よむ", "romaji": "yomu", "meaning": "membaca", "category": "verb"},
    {"word": "話す", "reading": "はなす", "romaji": "hanasu", "meaning": "berbicara", "category": "verb"},
    {"word": "聞く", "reading": "きく", "romaji": "kiku", "meaning": "mendengar/menjawab", "category": "verb"},
    {"word": "行く", "reading": "いく", "romaji": "iku", "meaning": "pergi", "category": "verb"},
]

N5_GRAMMAR_PATTERNS = [
    {"pattern": "は", "usage": "topik marker (wa)", "example": "私は学生です", "meaning": "Saya adalah mahasiswa"},
    {"pattern": "が", "usage": "subjek marker (ga)", "example": "私が学生です", "meaning": "Saya yang mahasiswa"},
    {"pattern": "を", "usage": "objek marker (wo)", "example": "水を飲みます", "meaning": "Minum air"},
    {"pattern": "に", "usage": "arah/tujuan (ni)", "example": "大学に行きます", "meaning": "Pergi ke universitas"},
    {"pattern": "で", "usage": "tempat/alat (de)", "example": "バスで行きます", "meaning": "Pergi dengan bus"},
    {"pattern": "と", "usage": "dan/dengan (to)", "example": "友達と話します", "meaning": "Bicara dengan teman"},
    {
        "pattern": "や",
        "usage": "dan (sebagian) (ya)",
        "example": "苹果やみかん",
        "meaning": "Apel dan jeruk (sebagian)",
    },
    {
        "pattern": "から",
        "usage": "karena/dari (kara)",
        "example": "忙しいから行けません",
        "meaning": "Karena sibuk tidak bisa pergi",
    },
    {"pattern": "まで", "usage": "sampai (made)", "example": "5時まで勉強します", "meaning": "Belajar sampai jam 5"},
    {"pattern": "も", "usage": "juga (mo)", "example": "私も学生です", "meaning": "Saya juga mahasiswa"},
    {"pattern": "ね", "usage": "penegasan/permintaan setuju (ne)", "example": "美味しいね", "meaning": "Enak ya"},
    {"pattern": "よ", "usage": "penegasan (yo)", "example": "明日来ますよ", "meaning": "Besok akan datang"},
    {"pattern": "か", "usage": "tanya (ka)", "example": "何をしますか", "meaning": "Apa yang dilakukan?"},
    {
        "pattern": "ですが",
        "usage": "tetapi (desu ga)",
        "example": "行きたいですが、忙しです",
        "meaning": "Mau pergi, tapi sibuk",
    },
]

LESSON_TEMPLATES = {
    "greetings": {
        "title": "Salam dan Ucapan Sehari-hari",
        "vocab": ["こんにちは", "おはよう", "こんばんは", "さようなら", "ありがとう"],
        "grammar": ["は", "の"],
    },
    "self_introduction": {
        "title": "Perkenalan Diri (Jikoshoukai)",
        "vocab": ["名前", "国籍", "出身", "年齢", "職業"],
        "grammar": ["は", "です", "が"],
    },
    "numbers": {
        "title": "Angka dan Bilangan",
        "vocab": ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"],
        "grammar": ["を", "で"],
    },
}
