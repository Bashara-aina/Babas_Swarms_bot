"""Furigana and Romaji annotation for Japanese text."""

import re


def annotate_japanese(text: str, show_furigana: bool = True, show_romaji: bool = True) -> str:
    try:
        import pykakasi

        kks = pykakasi.kakasi()
        result = kks.convert(text)

        output_parts = []
        for item in result:
            orig = item.get("orig", "")
            hira = item.get("hira", "")
            hepburn = item.get("hepburn", "")

            if orig == hira or not hira:
                output_parts.append(orig)
            else:
                part = orig
                if show_furigana and hira:
                    part += f"({hira})"
                if show_romaji and hepburn:
                    part += f" [{hepburn}]"
                output_parts.append(part)

        return "".join(output_parts)

    except ImportError:
        return f"{text} [pykakasi not installed]"
    except Exception:
        return text


def extract_japanese_only(text: str) -> str:
    jp_pattern = re.compile(
        r"[\u3040-\u309F"
        r"\u30A0-\u30FF"
        r"\u4E00-\u9FFF"
        r"\u3000-\u303F"
        r"\uFF01-\uFF0F"
        r"\uFF1A-\uFF20"
        r"\uFF3B-\uFF40"
        r"\uFF5B-\uFF65"
        r"\s]+"
    )
    matches = jp_pattern.findall(text)
    return " ".join(matches).strip()


N5_EXAMPLE_VOCAB = [
    ("学生", "がくせい", "gakusei", "mahasiswa/murid"),
    ("先生", "せんせい", "sensei", "guru/dosen"),
    ("大学", "だいがく", "daigaku", "universitas"),
    ("日本語", "にほんご", "nihongo", "bahasa Jepang"),
    ("食べる", "たべる", "taberu", "makan"),
    ("飲む", "のむ", "nomu", "minum"),
    ("行く", "いく", "iku", "pergi"),
    ("来る", "くる", "kuru", "datang"),
    ("見る", "みる", "miru", "melihat"),
    ("込む", "こむ", "komu", "penuh sesak"),
]
