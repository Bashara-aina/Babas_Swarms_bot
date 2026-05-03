"""Regression tests for rumahlabuh question-difference checks in posts 5 and 6."""

import pytest

from tools.rumahlabuh_thread_generator import ThreadValidator, load_config


@pytest.fixture
def validator():
    config = load_config()
    return ThreadValidator(config)


class TestPost5MustContainQuestion:
    def test_post_5_without_question_fails(self, validator):
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 No question here",
            "6/6 rumahlabuh.com?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 must contain question" in errors

    def test_post_5_with_question_passes(self, validator):
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 What do you think?",
            "6/6 rumahlabuh.com?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 must contain question" not in errors


class TestPost6MustContainQuestion:
    def test_post_6_without_question_fails(self, validator):
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 What do you think?",
            "6/6 rumahlabuh.com no question",
        ]
        errors = validator.validate(thread)
        assert "Post 6 must contain question" in errors

    def test_post_6_with_question_passes(self, validator):
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 What do you think?",
            "6/6 rumahlabuh.com and you?",
        ]
        errors = validator.validate(thread)
        assert "Post 6 must contain question" not in errors


class TestQ5AndQ6MustBeDifferent:
    def test_same_first_question_fails(self, validator):
        """When both posts start with same question text, validation should fail."""
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 Lo suka kost yang mana?",
            "6/6 Lo suka kost yang mana?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 and post 6 questions must be different" in errors

    def test_different_first_question_passes(self, validator):
        """Different first questions should pass validation."""
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 Lo suka kost yang mana?",
            "6/6 Kamu biasanya milih apa?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 and post 6 questions must be different" not in errors

    def test_question_with_extra_text_same_first_part_fails(self, validator):
        """When the identical first question is extended with more text, validation should fail."""
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 Lo pernah nyari kost di Solo?",
            "6/6 Lo pernah nyari kost di Solo? dan还要 tanya ke penghuni",
        ]
        errors = validator.validate(thread)
        assert "Post 5 and post 6 questions must be different" in errors

    def test_totally_different_questions_pass(self, validator):
        """Totally different questions should pass."""
        thread = [
            "1/6 Normal first post",
            "2/6 Normal second",
            "3/6 Normal third",
            "4/6 Normal fourth",
            "5/6 Berapa budget lo per bulan?",
            "6/6 Deket kampus mana aja?",
        ]
        errors = validator.validate(thread)
        assert "Post 5 and post 6 questions must be different" not in errors


class TestFirstQuestionTextExtraction:
    """Tests for _first_question_text helper function behavior."""

    def test_extracts_first_question(self):
        from tools.rumahlabuh_thread_generator import _first_question_text

        post = "Lo suka kost yang mana? Gue sih suka yang deket kampus."
        result = _first_question_text(post)
        assert result == "lo suka kost yang mana"

    def test_empty_when_no_question(self):
        from tools.rumahlabuh_thread_generator import _first_question_text

        post = "Ini post tanpa pertanyaan"
        result = _first_question_text(post)
        assert result == ""

    def test_strips_and_lowercases(self):
        from tools.rumahlabuh_thread_generator import _first_question_text

        post = "  APA ITU? Jawaban: banyak hal"
        result = _first_question_text(post)
        assert result == "apa itu"

    def test_only_first_question_matters(self):
        from tools.rumahlabuh_thread_generator import _first_question_text

        post = "Pertama? Kedua? Ketiga?"
        result = _first_question_text(post)
        assert result == "pertama"


class TestValidationIntegration:
    def test_complete_validation_with_questions(self, validator):
        """Full validation with correct question format."""
        thread = [
            "1/6 Gue pernah zonk pas nyari kost",
            "2/6 Foto keliatan rapi, realitanya beda",
            "3/6 Checklist: deposit, akses, lingkungan",
            "4/6 Detail kecil yang sering orang skip",
            "5/6 Lo lebih suka Cek Sendiri atau Tanya Penguni?",
            "6/6 RumahLabuh.com bisa bantu Compare. Lo sering zonk di mana?",
        ]
        errors = validator.validate(thread)
        # Should pass or only fail on brand/pronoun rules
        critical_errors = [e for e in errors if "question" in e.lower()]
        assert len(critical_errors) == 0
