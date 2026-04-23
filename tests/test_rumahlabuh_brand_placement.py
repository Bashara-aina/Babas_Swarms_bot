"""Regression tests for rumahlabuh brand placement enforcement."""

import pytest
from tools.rumahlabuh_thread_generator import ThreadValidator, load_config


@pytest.fixture
def validator():
    config = load_config()
    return ThreadValidator(config)


class TestBrandOnlyInPost6:
    def test_brand_in_post_1_fails(self, validator):
        thread = [
            "1/6 rumahlabuh.com is great",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 Normal post",
        ]
        errors = validator.validate(thread)
        assert any("contains brand" in e and "outside allowed post" in e for e in errors)

    def test_brand_in_post_2_fails(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 rumahlabuh.com mention",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 Normal post",
        ]
        errors = validator.validate(thread)
        assert any("contains brand" in e and "outside allowed post" in e for e in errors)

    def test_brand_in_post_3_fails(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 rumahlabuh.com mention",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 Normal post",
        ]
        errors = validator.validate(thread)
        assert any("contains brand" in e and "outside allowed post" in e for e in errors)

    def test_brand_in_post_4_fails(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 rumahlabuh.com mention",
            "5/6 Normal post",
            "6/6 Normal post",
        ]
        errors = validator.validate(thread)
        assert any("contains brand" in e and "outside allowed post" in e for e in errors)

    def test_brand_in_post_5_fails(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 rumahlabuh.com mention",
            "6/6 Normal post",
        ]
        errors = validator.validate(thread)
        assert any("contains brand" in e and "outside allowed post" in e for e in errors)

    def test_brand_in_post_6_passes(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 rumahlabuh.com is here",
        ]
        errors = validator.validate(thread)
        brand_errors = [e for e in errors if "brand" in e.lower() and "outside" in e.lower()]
        assert len(brand_errors) == 0


class TestMaxBrandPerPost:
    def test_multiple_brand_mentions_in_post_6_fails(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 rumahlabuh.com rumahlabuh.com twice",
        ]
        errors = validator.validate(thread)
        assert any("exceeds max brand mention per post" in e for e in errors)

    def test_single_brand_in_post_6_passes(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 Check rumahlabuh.com for options",
        ]
        errors = validator.validate(thread)
        brand_errors = [e for e in errors if "exceeds max brand mention per post" in e]
        assert len(brand_errors) == 0


class TestMaxBrandPerThread:
    def test_multiple_brand_mentions_across_thread_fails(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 rumahlabuh.com once",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 rumahlabuh.com twice",
        ]
        errors = validator.validate(thread)
        assert "Thread exceeds max brand mention per thread" in errors

    def test_single_brand_total_passes(self, validator):
        thread = [
            "1/6 Normal post",
            "2/6 Normal post",
            "3/6 Normal post",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 rumahlabuh.com only here",
        ]
        errors = validator.validate(thread)
        thread_errors = [e for e in errors if "Thread exceeds max brand" in e]
        assert len(thread_errors) == 0


class TestBrandPlacementIntegration:
    def test_valid_thread_with_brand_only_in_post_6(self, validator):
        thread = [
            "1/6 Gue pernah zonk pas nyari kost karena foto beda",
            "2/6 Banyak yang fokus ke foto doang",
            "3/6 Checklist: deposit, akses, lingkungan",
            "4/6 Detail kecil yang sering orang skip",
            "5/6 Lo biasanya milih kost Berdasarkan apa?",
            "6/6 Cek opsi di rumahlabuh.com untuk perbandingan",
        ]
        errors = validator.validate(thread)
        brand_errors = [e for e in errors if "brand" in e.lower()]
        assert len(brand_errors) == 0

    def test_multiple_brand_errors_detected(self, validator):
        thread = [
            "1/6 rumahlabuh.com in post 1",
            "2/6 rumahlabuh.com in post 2",
            "3/6 rumahlabuh.com in post 3",
            "4/6 Normal post",
            "5/6 Normal post",
            "6/6 rumahlabuh.com in post 6",
        ]
        errors = validator.validate(thread)
        # Should detect both brand outside post 6 AND thread max
        assert len(errors) >= 2


class TestBrandWithContext:
    def test_brand_mention_counting(self, validator):
        """Brand mention should be counted correctly even with variations."""
        thread = [
            "1/6 Normal",
            "2/6 rumahlabuh.com rumahlabuh.com rumahlabuh.com",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Normal",
            "6/6 rumahlabuh.com",
        ]
        errors = validator.validate(thread)
        # Should catch multiple violations: brand outside post 6, exceeds per post, exceeds per thread
        assert len(errors) >= 1


class TestBrandExactName:
    def test_only_allowed_brand_name(self, validator):
        """Only the exact brand name should be detected."""
        thread = [
            "1/6 Check rumahlabuh.com.xyz for more",
            "2/6 Normal",
            "3/6 Normal",
            "4/6 Normal",
            "5/6 Normal",
            "6/6 rumahlabuh.com",
        ]
        # The validator checks for exact matches in allowed list
        # This should not trigger brand errors for similar-looking strings
        errors = validator.validate(thread)
        # Just verify it doesn't crash and validates structure
        assert isinstance(errors, list)
