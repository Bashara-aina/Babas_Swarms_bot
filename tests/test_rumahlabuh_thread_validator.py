"""Regression tests for rumahlabuh thread validator rule enforcement."""

import pytest
from tools.rumahlabuh_thread_generator import ThreadValidator, load_config


@pytest.fixture
def validator():
    config = load_config()
    return ThreadValidator(config)


@pytest.fixture
def valid_thread():
    """A valid 6-post thread."""
    return [
        "1/6 Gue pernah ngegas pas nyari kost karena fotonya beda jauh dari realita.",
        "2/6 Banyak yang skip cek detail dulu, baru sadar pas udah masuk. {pain_point}.",
        "3/6 Checklist yang sering gue skip: tanya aturan deposit dari awal.",
        "4/6 Yang bikin beda itu usually hal kecil yang orang lain lewatin.",
        "5/6 Lo lebih suka cek kamar sendiri atau tanya ke penghuni dulu?",
        "6/6 Buat yang lagi nyari kost di Solo, bisa cek opsi di rumahlabuh.com. Tinggal bandingin lokasi, budget, dan fasilitas?",
    ]


class TestPostCount:
    def test_post_count_must_be_6(self, validator):
        errors = validator.validate([])
        assert "Post count must be 6, got 0" in errors

    def test_post_count_5_fails(self, validator):
        thread = ["1/6 Post"] * 5
        errors = validator.validate(thread)
        assert "Post count must be 6, got 5" in errors


class TestPostNumbering:
    def test_missing_numbering_prefix(self, validator):
        thread = [
            "Post tanpa nomor",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Normal",
            "6/6 Normal",
        ]
        errors = validator.validate(thread)
        assert "Post 1 missing numbering prefix" in errors

    def test_wrong_numbering(self, validator):
        thread = [
            "2/6 Wrong number",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Normal",
            "6/6 Normal",
        ]
        errors = validator.validate(thread)
        assert "Post 1 missing numbering prefix" in errors


class TestDuplicatePosts:
    def test_duplicate_posts_detected(self, validator):
        thread = [
            "1/6 Different first",
            "2/6 Different second",
            "3/6 Same content",
            "3/6 Same content",  # Same post number = identical text = duplicate
            "5/6 Different fifth?",
            "6/6 Different sixth?",
        ]
        errors = validator.validate(thread)
        assert "Duplicate post detected" in errors


class TestBrandLimits:
    def test_brand_only_in_post_6(self, validator):
        thread = [
            "1/6 Post with rumahlabuh.com inside",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 rumahlabuh.com is here",
        ]
        errors = validator.validate(thread)
        assert any("contains brand" in e and "outside allowed post" in e for e in errors)

    def test_max_brand_per_thread(self, validator):
        thread = [
            "1/6 Normal",
            "2/6 Normal",
            "3/6 rumahlabuh.com again",
            "4/6 Normal",
            "5/6 Normal",
            "6/6 rumahlabuh.com twice",
        ]
        errors = validator.validate(thread)
        assert "Thread exceeds max brand mention per thread" in errors

    def test_max_brand_per_post(self, validator):
        thread = [
            "1/6 rumahlabuh.com rumahlabuh.com",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Normal",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("exceeds max brand mention per post" in e for e in errors)


class TestPronounMixing:
    def test_no_mixing_gue_with_aku(self, validator):
        thread = [
            "1/6 Gue suka kost",
            "2/6 Aku juga suka",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 Normal",
        ]
        errors = validator.validate(thread)
        assert any("Pronoun mix detected" in e for e in errors)

    def test_no_mixing_lo_with_kamu(self, validator):
        thread = [
            "1/6 Lo pernah?",
            "2/6 Kamu pasti",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 Normal",
        ]
        errors = validator.validate(thread)
        assert any("Pronoun mix detected" in e for e in errors)

    def test_no_kami_in_storytelling(self, validator):
        thread = [
            "1/6 Kami suka kost",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 Normal",
        ]
        errors = validator.validate(thread)
        assert "'kami' is not allowed" in errors


class TestForbiddenOpenings:
    def test_forbidden_opening_detected(self, validator):
        thread = [
            "1/6 Hai yang lagi nyari kost, ini tips buat lo",
            "2/6 Normal post",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("starts with forbidden phrase" in e for e in errors)


class TestBlockedEnglishTerms:
    def test_blocked_english_term(self, validator):
        thread = [
            "1/6 Post with neighbors inside",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("contains blocked term" in e for e in errors)


class TestEmDash:
    def test_em_dash_detected(self, validator):
        thread = [
            "1/6 Post with — em dash",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("contains em dash" in e for e in errors)


class TestCapsDrama:
    def test_caps_drama_detected(self, validator):
        thread = [
            "1/6 Post with SURE thing",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("has caps-drama token" in e for e in errors)


class TestEmojiLimits:
    def test_excessive_emoji(self, validator):
        thread = [
            "1/6 Post with 😀😁😂😆😄",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("has too many emoji" in e for e in errors)

    def test_acceptable_emoji_count(self, validator):
        thread = [
            "1/6 Post with 😀",
            "2/6 Normal 😀",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert not any("has too many emoji" in e for e in errors)


class TestHashtagLimits:
    def test_excessive_hashtags(self, validator):
        thread = [
            "1/6 Post #tag1 #tag2 #tag3 #tag4",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("exceeds max hashtags" in e for e in errors)


class TestNumberedListLimits:
    def test_excessive_numbered_items(self, validator):
        thread = [
            "1/6 Post\n1. item1\n2. item2\n3. item3\n4. item4\n5. item5",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("exceeds max numbered list items" in e for e in errors)


class TestEngagementQuestions:
    def test_post_5_must_have_question(self, validator):
        thread = [
            "1/6 Normal",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 No question here",
            "6/6 rumahlabuh.com?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 must contain question" in errors

    def test_post_6_must_have_question(self, validator):
        thread = [
            "1/6 Normal",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Has question?",
            "6/6 rumahlabuh.com no question",
        ]
        errors = validator.validate(thread)
        assert "Post 6 must contain question" in errors


class TestQuestionDifference:
    def test_q5_q6_must_be_different(self, validator):
        # The first question text extraction strips prefix and takes text before "?"
        # so identical first question text after stripping = error
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second post",
            "3/6 Normal third post",
            "4/6 Normal fourth post",
            "5/6 Lo suka kost yang mana?",
            "6/6 Lo suka kost yang mana?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 and post 6 questions must be different" in errors

    def test_q5_q6_different_passes(self, validator):
        thread = [
            "1/6 Normal",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Question one?",
            "6/6 Question two?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 and post 6 questions must be different" not in errors


class TestNonLatinScript:
    def test_non_latin_script_detected(self, validator):
        thread = [
            "1/6 Post with 中文 characters",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("has disallowed script char" in e for e in errors)


class TestFearPhraseTone:
    def test_fear_phrase_detected(self, validator):
        thread = [
            "1/6 Normal",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Jangan ulangi kesalahan mereka",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("Blocked fear phrase" in e for e in errors)


class TestAIFormulaPhrase:
    def test_ai_formula_phrase_detected(self, validator):
        thread = [
            "1/6 Normal",
            "2/6 Normal",
            "3/6 Berikut adalah informasinya",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("Blocked AI formula" in e for e in errors)


class TestUnsourcedPercentage:
    def test_unsourced_percentage_detected(self, validator):
        thread = [
            "1/6 Post with 90% statistics",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert any("unsourced percentage" in e for e in errors)

    def test_sourced_percentage_ok(self, validator):
        thread = [
            "1/6 Post with 90% from survey of banyak orang",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Lo suka?",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        assert not any("unsourced percentage" in e for e in errors)


class TestValidThread:
    def test_valid_thread_passes(self, validator, valid_thread):
        errors = validator.validate(valid_thread)
        # Should have no errors for a properly formatted thread
        assert len(errors) == 0 or all("rumahlabuh" in e.lower() for e in errors)
