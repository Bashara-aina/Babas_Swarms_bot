"""
rumahlabuh Thread Generator v8

Long-lasting design:
- No content copy is hardcoded in this Python file
- All narrative templates/phrases live in JSON blueprints
- Validation rules live in JSON config
- Rotation + history prevent repetitive daily output
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / "rumahlabuh_threads_v5.json"
FACTS_PATH = Path(__file__).parent.parent / ".claude" / "scripts" / "rumahlabuh-facts.md"


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _merge_dict(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in extra.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def _safe_choice(rng: random.Random, options: list[str], fallback: str) -> str:
    return rng.choice(options) if options else fallback


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip()


def _first_question_text(post: str) -> str:
    if "?" not in post:
        return ""
    return post.split("?", 1)[0].strip().lower()


def _count_numbered_items(post: str) -> int:
    return sum(1 for line in post.splitlines() if re.match(r"^\s*\d+[.)]\s+", line))


def _count_hashtags(post: str) -> int:
    return len(re.findall(r"(?:^|\s)#[\w_]+", post))


def _contains_whole_term(text: str, term: str) -> bool:
    escaped = re.escape(term.strip().lower())
    if not escaped:
        return False
    return re.search(rf"(?<!\w){escaped}(?!\w)", text.lower()) is not None


def _is_disallowed_script_char(ch: str) -> bool:
    if ord(ch) < 128:
        return False
    if ch.isspace():
        return False
    name = unicodedata.name(ch, "")
    if "LATIN" in name:
        return False
    if "EMOJI" in name or unicodedata.category(ch) == "So":
        return False
    blocked_scripts = ("CJK", "HIRAGANA", "KATAKANA", "ARABIC", "DEVANAGARI", "THAI", "CYRILLIC", "HEBREW")
    return any(script in name for script in blocked_scripts)


def _render_template(template: str, ctx: dict[str, str]) -> str:
    class SafeDict(dict):
        def __missing__(self, key: str) -> str:  # pragma: no cover
            return "{" + key + "}"

    return template.format_map(SafeDict(**ctx))


def _signature(thread: list[str]) -> str:
    joined = "\n".join(_normalize(p).lower() for p in thread)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


@dataclass
class GeneratorPaths:
    blueprint_path: Path
    history_path: Path


class FactsExtractor:
    def __init__(self, facts_text: str):
        self.text = facts_text

    def get_price_min(self) -> str:
        for line in self.text.splitlines():
            if "Bulanan mulai" in line and ":" in line:
                val = line.split(":", 1)[1].strip().split()[0]
                return val.replace("**", "").replace("*", "")
        return "Rp800rb"

    def get_city(self) -> str:
        return "Solo"

    def get_area(self) -> str:
        for candidate in ("Kentingan", "Jebres", "Banjarsari", "Laweyan", "Pabelan", "Mojosongo"):
            if candidate.lower() in self.text.lower():
                return candidate
        return "Kentingan"

    def get_facilities(self) -> list[str]:
        facilities: list[str] = []
        for line in self.text.splitlines():
            if line.strip().startswith("-"):
                val = line.strip().lstrip("-").strip()
                if val:
                    facilities.append(val)
        return facilities[:10] if facilities else ["WiFi", "AC", "kamar mandi dalam", "parkir motor"]


class HistoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load_or_init()

    def _load_or_init(self) -> dict[str, Any]:
        if self.path.exists():
            return load_json(self.path)
        data = {"items": []}
        dump_json(self.path, data)
        return data

    def save(self) -> None:
        dump_json(self.path, self.data)

    def was_signature_used_recently(self, sig: str, within_days: int, today: date) -> bool:
        cutoff = today - timedelta(days=within_days)
        for item in self.data.get("items", []):
            try:
                d = datetime.strptime(item["date"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            if d >= cutoff and item.get("signature") == sig:
                return True
        return False

    def last_techniques(self, within_days: int, today: date) -> list[str]:
        cutoff = today - timedelta(days=within_days)
        out: list[str] = []
        for item in self.data.get("items", []):
            try:
                d = datetime.strptime(item["date"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            if d >= cutoff and isinstance(item.get("technique"), str):
                out.append(item["technique"])
        return out

    def append(self, sig: str, technique: str, today: date) -> None:
        self.data.setdefault("items", [])
        self.data["items"].append({"date": today.strftime("%Y-%m-%d"), "signature": sig, "technique": technique})
        self.data["items"] = self.data["items"][-500:]
        self.save()


class BlueprintGenerator:
    def __init__(self, config: dict[str, Any], facts_text: str):
        self.config = config
        self.rules = config["rules"]
        self.language = config.get("language", {})
        self.generator_cfg = config.get("generator", {})
        self.facts = FactsExtractor(facts_text)

        blueprint_path = Path(__file__).parent / self.generator_cfg.get("blueprint_file", "rumahlabuh_thread_blueprints.json")
        history_path = Path(__file__).parent / self.generator_cfg.get("history_file", "rumahlabuh_thread_history.json")
        self.paths = GeneratorPaths(blueprint_path=blueprint_path, history_path=history_path)
        self.blueprint = load_json(self.paths.blueprint_path)
        self.history = HistoryStore(self.paths.history_path)

    def _pick_pronouns(self, rng: random.Random) -> tuple[str, str]:
        pronouns = self.rules["pronouns"]
        informal = pronouns["informal"]
        semi = pronouns["semi_formal"]
        if rng.random() < self.generator_cfg.get("pronoun_informal_ratio", 0.85):
            return informal[0], informal[1]
        return semi[0], semi[1]

    def _build_context(self, rng: random.Random, p1: str, p2: str) -> dict[str, str]:
        pools = self.blueprint.get("pools", {})
        brand = self.rules["brand_mention"]["allowed"][0]
        def pick_and_render(key: str, fallback: str) -> str:
            raw = _safe_choice(rng, pools.get(key, []), fallback)
            return _render_template(raw, {"brand": brand})

        facilities = self.facts.get_facilities()
        facility_1 = _safe_choice(rng, facilities, "WiFi")
        facility_2 = _safe_choice(rng, [x for x in facilities if x != facility_1], "AC")
        facility_3 = _safe_choice(rng, [x for x in facilities if x not in {facility_1, facility_2}], "kamar mandi dalam")

        ctx = {
            "p1": p1,
            "p2": p2,
            "brand": brand,
            "city": self.facts.get_city(),
            "area": self.facts.get_area(),
            "price_min": self.facts.get_price_min(),
            "facility_1": facility_1,
            "facility_2": facility_2,
            "facility_3": facility_3,
            "pain_point": _safe_choice(rng, pools.get("pain_points", []), "foto listing beda dari realita"),
            "pain_point_2": _safe_choice(rng, pools.get("pain_points_2", []), "biaya tambahan baru ketahuan belakangan"),
            "insight": _safe_choice(rng, pools.get("insights", []), "yang bikin betah biasanya faktor harian, bukan cuma foto"),
            "check_1": _safe_choice(rng, pools.get("checks", []), "cek kondisi kamar mandi"),
            "check_2": _safe_choice(rng, pools.get("checks_2", []), "tanya aturan deposit"),
            "check_3": _safe_choice(rng, pools.get("checks_3", []), "cek suasana jam malam"),
            "landmark": _safe_choice(rng, pools.get("landmarks", []), "UNS"),
            "cta_soft": pick_and_render("cta_soft", "bisa cek opsi yang lebih rapi di {brand}"),
            "cta_soft_2": pick_and_render("cta_soft_2", "tinggal bandingin lokasi, budget, dan fasilitas"),
        }
        return ctx

    def _apply_replacements(self, text: str) -> str:
        replacements = self.language.get("replacements", {})
        out = text.replace("—", "-")
        for src, dst in replacements.items():
            out = re.sub(rf"(?<!\w){re.escape(src)}(?!\w)", dst, out, flags=re.IGNORECASE)
        return _normalize(out)

    def _select_technique(self, today: date, rng: random.Random) -> dict[str, Any]:
        techniques = self.blueprint.get("techniques", [])
        if not techniques:
            raise ValueError("No techniques found in blueprint")

        rotation = self.generator_cfg.get("rotation", {})
        if rotation.get("enabled", True):
            names = [t["name"] for t in techniques]
            base_idx = today.toordinal() % len(names)
            ordered = names[base_idx:] + names[:base_idx]
            recent = set(self.history.last_techniques(rotation.get("avoid_repeat_days", 7), today))
            candidate_name = next((n for n in ordered if n not in recent), ordered[0])
            chosen = next(t for t in techniques if t["name"] == candidate_name)
            return chosen

        total = sum(int(t.get("weight", 1)) for t in techniques)
        pick = rng.randint(1, max(total, 1))
        acc = 0
        for t in techniques:
            acc += int(t.get("weight", 1))
            if pick <= acc:
                return t
        return techniques[0]

    def generate(self, today: date | None = None) -> dict[str, Any]:
        today = today or date.today()
        max_attempts = int(self.generator_cfg.get("max_attempts", 120))
        dedupe_window = int(self.generator_cfg.get("dedupe_window_days", 60))

        for attempt in range(max_attempts):
            rng = random.Random(f"{today.isoformat()}:{attempt}")
            technique = self._select_technique(today, rng)
            p1, p2 = self._pick_pronouns(rng)
            ctx = self._build_context(rng, p1, p2)

            posts: list[str] = []
            templates = technique.get("posts", {})
            for idx in range(1, 7):
                choices = templates.get(str(idx), [])
                selected = _safe_choice(rng, choices, f"{idx}/6")
                rendered = _render_template(selected, ctx)
                posts.append(self._apply_replacements(rendered))

            # Ensure q5 != q6 if both contain question
            if "?" in posts[4] and "?" in posts[5]:
                if _first_question_text(posts[4]) == _first_question_text(posts[5]):
                    continue

            sig = _signature(posts)
            if self.history.was_signature_used_recently(sig, dedupe_window, today):
                continue

            result = {
                "success": True,
                "thread": posts,
                "pronouns": [p1, p2],
                "technique": technique["name"],
                "signature": sig,
                "date": today.isoformat(),
            }
            return result

        return {"success": False, "errors": [f"Could not build unique thread after {max_attempts} attempts"]}

    def mark_used(self, result: dict[str, Any]) -> None:
        if not result.get("success"):
            return
        self.history.append(result["signature"], result["technique"], datetime.strptime(result["date"], "%Y-%m-%d").date())


class ThreadValidator:
    def __init__(self, config: dict[str, Any]):
        self.rules = config["rules"]
        self.language = config.get("language", {})

    def validate(self, thread: list[str]) -> list[str]:
        errors: list[str] = []
        structure = self.rules["structure"]
        validation = self.rules.get("validation", {})
        punctuation = self.rules["punctuation"]
        tone = self.rules["tone"]
        pronouns = self.rules["pronouns"]
        stats = self.rules["stats"]

        if len(thread) != structure["exact_post_count"]:
            return [f"Post count must be {structure['exact_post_count']}, got {len(thread)}"]

        for i, post in enumerate(thread, start=1):
            if not post.startswith(f"{i}/6"):
                errors.append(f"Post {i} missing numbering prefix")

        if validation.get("no_duplicate_posts", True):
            if len(set(_normalize(p.lower()) for p in thread)) != len(thread):
                errors.append("Duplicate post detected")

        # brand mention
        brand_cfg = self.rules["brand_mention"]
        total_brand = 0
        for idx, post in enumerate(thread, start=1):
            for brand in brand_cfg["allowed"]:
                cnt = post.count(brand)
                total_brand += cnt
                if cnt > 0 and idx != brand_cfg["only_in_post"]:
                    errors.append(f"Post {idx} contains brand '{brand}' outside allowed post")
                if cnt > brand_cfg["max_per_post"]:
                    errors.append(f"Post {idx} exceeds max brand mention per post")
        if total_brand > brand_cfg["max_per_thread"]:
            errors.append("Thread exceeds max brand mention per thread")

        # pronoun consistency
        text_all = " ".join(thread).lower()
        found_informal = {p for p in pronouns["informal"] if _contains_whole_term(text_all, p)}
        found_semi = {p for p in pronouns["semi_formal"] if _contains_whole_term(text_all, p)}
        if pronouns.get("no_mixing", True) and found_informal and found_semi:
            errors.append(f"Pronoun mix detected: {found_informal} + {found_semi}")
        if pronouns.get("no_kami_in_storytelling", True) and _contains_whole_term(text_all, "kami"):
            errors.append("'kami' is not allowed")

        # forbidden openings
        for idx, post in enumerate(thread, start=1):
            start = post[:120].lower()
            for phrase in self.rules["opening"]["forbidden"]:
                if phrase.lower() in start:
                    errors.append(f"Post {idx} starts with forbidden phrase '{phrase}'")
                    break

        # blocked terms
        blocked_terms = [x.lower().strip() for x in self.rules.get("english_blocked", []) if x.strip()]
        for idx, post in enumerate(thread, start=1):
            for term in blocked_terms:
                if _contains_whole_term(post, term):
                    errors.append(f"Post {idx} contains blocked term '{term}'")
                    break

        # punctuation + emoji + caps
        allowed_acronyms = set(x.lower() for x in self.language.get("allowed_acronyms", ["wifi", "ac", "cctv", "ums", "uns"]))
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]"
        )
        for idx, post in enumerate(thread, start=1):
            if punctuation.get("no_em_dash", True) and "—" in post:
                errors.append(f"Post {idx} contains em dash")

            if punctuation.get("no_caps_for_drama", True):
                for token in post.split():
                    clean = re.sub(r"[^\w]", "", token)
                    if len(clean) > 2 and clean.isupper() and clean.lower() not in allowed_acronyms:
                        errors.append(f"Post {idx} has caps-drama token '{token}'")
                        break

            if punctuation.get("no_excessive_emoji", True):
                if len(emoji_pattern.findall(post)) > 2:
                    errors.append(f"Post {idx} has too many emoji")

        # structure limits
        max_tags = validation.get("max_hashtags_per_post", 3)
        max_num = validation.get("max_numbered_list_items_per_post", 4)
        for idx, post in enumerate(thread, start=1):
            if _count_hashtags(post) > max_tags:
                errors.append(f"Post {idx} exceeds max hashtags {max_tags}")
            if _count_numbered_items(post) > max_num:
                errors.append(f"Post {idx} exceeds max numbered list items {max_num}")

        # engagement Q checks
        if structure.get("engagement_question_post_5", True) and "?" not in thread[4]:
            errors.append("Post 5 must contain question")
        if structure.get("engagement_question_post_6", True) and "?" not in thread[5]:
            errors.append("Post 6 must contain question")
        if structure.get("engagement_question_post_5_different", True):
            if _first_question_text(thread[4]) == _first_question_text(thread[5]):
                errors.append("Post 5 and post 6 questions must be different")

        # character script gate
        if self.rules.get("character_encoding", {}).get("no_non_latin", True):
            for idx, post in enumerate(thread, start=1):
                bad = next((ch for ch in post if _is_disallowed_script_char(ch)), None)
                if bad is not None:
                    errors.append(f"Post {idx} has disallowed script char {repr(bad)}")

        # tone gate
        for phrase in tone.get("no_menakut_takuti", []):
            if phrase.lower() in text_all:
                errors.append(f"Blocked fear phrase found '{phrase}'")
        for phrase in tone.get("no_ai_formulas", []):
            if phrase.lower() in text_all:
                errors.append(f"Blocked AI formula found '{phrase}'")

        # unsourced %
        if stats.get("no_unsourced_percentages", True):
            pct_pattern = re.compile(r"\d+\s*%")
            allowed_sources = [x.lower() for x in stats.get("allowed_phrases", [])]
            for idx, post in enumerate(thread, start=1):
                if pct_pattern.search(post):
                    if not any(src in post.lower() for src in allowed_sources):
                        errors.append(f"Post {idx} has unsourced percentage")

        return errors


def load_config() -> dict[str, Any]:
    cfg = load_json(CONFIG_PATH)
    defaults = {
        "generator": {
            "blueprint_file": "rumahlabuh_thread_blueprints.json",
            "history_file": "rumahlabuh_thread_history.json",
            "pronoun_informal_ratio": 0.85,
            "max_attempts": 120,
            "dedupe_window_days": 60,
            "rotation": {"enabled": True, "avoid_repeat_days": 7},
        },
        "language": {
            "replacements": {
                "about": "soal",
                "here": "di sini",
                "based on": "berdasarkan",
                "or maybe": "atau mungkin",
                "raise your hand": "",
                "no spam": "",
                "just actual data": "",
                "twice think": "pikir dua kali",
                "owner": "pemilik",
                "proxy-kan": "dibayangin",
                "prioritize": "utamakan",
                "sorpresa": "kejutan",
                "campus": "kampus",
                "neighbors": "tetangga",
                "experience": "pengalaman",
            },
            "allowed_acronyms": ["wifi", "ac", "cctv", "ums", "uns"],
        },
    }
    return _merge_dict(defaults, cfg)


def load_facts() -> str:
    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def generate_fresh_thread(save_history: bool = True) -> dict[str, Any]:
    config = load_config()
    facts_text = load_facts()
    generator = BlueprintGenerator(config, facts_text)
    validator = ThreadValidator(config)

    result = generator.generate()
    if not result.get("success"):
        return result

    errors = validator.validate(result["thread"])
    if errors:
        return {"success": False, "errors": errors, "thread": result["thread"]}

    if save_history:
        generator.mark_used(result)

    return result


if __name__ == "__main__":
    result = generate_fresh_thread(save_history=True)
    if result["success"]:
        print("Generated thread:")
        for i, post in enumerate(result["thread"], start=1):
            print(f"  {i}/6: {post}")
        print(f"\nPronouns: {tuple(result['pronouns'])}")
        print(f"Technique: {result['technique']}")
        print(f"Signature: {result['signature'][:10]}...")
    else:
        print("Generation failed:")
        for err in result["errors"]:
            print(f"  - {err}")
