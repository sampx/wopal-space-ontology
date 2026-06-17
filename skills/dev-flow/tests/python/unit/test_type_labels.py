#!/usr/bin/env python3
# test_type_labels.py - Test type normalization and label mapping

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from labels import (
    normalize_plan_type,
    plan_type_to_issue_label,
    issue_label_to_plan_type,
    ValidationError
)


# Parametrized test data: (input, expected_output)
NORMALIZE_CASES = [
    ("feat", "feature"),
    ("feature", "feature"),
    ("enhance", "enhance"),
    ("enhancement", "enhance"),
    ("fix", "fix"),
    ("bug", "fix"),
    ("perf", "perf"),
    ("performance", "perf"),
    ("refactor", "refactor"),
    ("docs", "docs"),
    ("doc", "docs"),
    ("documentation", "docs"),
    ("chore", "chore"),
    ("ci", "chore"),
    ("test", "test"),
]

PLAN_TYPE_TO_LABEL_CASES = [
    ("feature", "type/feature"),
    ("enhance", "type/feature"),
    ("fix", "type/bug"),
    ("perf", "type/perf"),
    ("refactor", "type/refactor"),
    ("docs", "type/docs"),
    ("test", "type/test"),
    ("chore", "type/chore"),
]

LABEL_TO_PLAN_TYPE_CASES = [
    ("type/feature", "feature"),
    ("type/bug", "fix"),
    ("type/perf", "perf"),
    ("type/refactor", "refactor"),
    ("type/docs", "docs"),
    ("type/test", "test"),
    ("type/chore", "chore"),
]


class TestNormalizePlanType(unittest.TestCase):
    """Test normalize_plan_type function"""

    def test_normalization_mapping(self):
        """normalize_plan_type correctly maps all supported types"""
        for input_type, expected in NORMALIZE_CASES:
            with self.subTest(input=input_type, expected=expected):
                self.assertEqual(normalize_plan_type(input_type), expected)

    def test_invalid_type_raises_error(self):
        """normalize_plan_type raises ValidationError for invalid type"""
        with self.assertRaises(ValidationError):
            normalize_plan_type("invalid")

    def test_empty_type_raises_error(self):
        """normalize_plan_type raises ValidationError for empty type"""
        with self.assertRaises(ValidationError):
            normalize_plan_type("")

    def test_case_insensitive(self):
        """normalize_plan_type is case insensitive"""
        self.assertEqual(normalize_plan_type("FEAT"), "feature")
        self.assertEqual(normalize_plan_type("Feature"), "feature")
        self.assertEqual(normalize_plan_type("FIX"), "fix")


class TestPlanTypeToIssueLabel(unittest.TestCase):
    """Test plan_type_to_issue_label function"""

    def test_label_mapping(self):
        """plan_type_to_issue_label correctly maps all canonical types"""
        for plan_type, expected_label in PLAN_TYPE_TO_LABEL_CASES:
            with self.subTest(plan_type=plan_type, expected=expected_label):
                self.assertEqual(plan_type_to_issue_label(plan_type), expected_label)

    def test_invalid_type_raises_error(self):
        """plan_type_to_issue_label raises ValidationError for invalid type"""
        with self.assertRaises(ValidationError):
            plan_type_to_issue_label("invalid")


class TestIssueLabelToPlanType(unittest.TestCase):
    """Test issue_label_to_plan_type function"""

    def test_label_mapping(self):
        """issue_label_to_plan_type correctly maps all supported labels"""
        for label, expected_type in LABEL_TO_PLAN_TYPE_CASES:
            with self.subTest(label=label, expected=expected_type):
                self.assertEqual(issue_label_to_plan_type(label), expected_type)

    def test_invalid_label_raises_error(self):
        """issue_label_to_plan_type raises ValidationError for invalid label"""
        with self.assertRaises(ValidationError):
            issue_label_to_plan_type("invalid")

    def test_unsupported_type_label_raises_error(self):
        """issue_label_to_plan_type raises ValidationError for unsupported type label"""
        with self.assertRaises(ValidationError):
            issue_label_to_plan_type("type/unknown")


class TestRoundTripConversion(unittest.TestCase):
    """Test round-trip conversion between plan type and issue label"""

    def test_round_trip_consistency(self):
        """Round-trip conversion preserves canonical types"""
        # Only test canonical types that have 1:1 mapping
        canonical_types = ["feature", "fix", "perf", "refactor", "docs", "test", "chore"]
        for plan_type in canonical_types:
            with self.subTest(plan_type=plan_type):
                label = plan_type_to_issue_label(plan_type)
                back = issue_label_to_plan_type(label)
                self.assertEqual(back, plan_type)

    def test_enhance_round_trip_maps_to_feature(self):
        """enhance -> type/feature -> feature (not enhance)"""
        # enhance is a sub-type of feature, so round-trip maps to feature
        label = plan_type_to_issue_label("enhance")
        back = issue_label_to_plan_type(label)
        self.assertEqual(back, "feature")


if __name__ == '__main__':
    unittest.main()
