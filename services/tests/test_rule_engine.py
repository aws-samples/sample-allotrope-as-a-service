# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import pytest


# ---------------------------------------------------------------------------
# resolve_path
# ---------------------------------------------------------------------------

class TestResolvePath:
    def test_simple_nested(self, rule_engine):
        data = {"a": {"b": 1}}
        results = rule_engine.resolve_path(data, "a.b")
        assert len(results) == 1
        path, val = results[0]
        assert val == 1
        assert "a" in path and "b" in path

    def test_top_level_key(self, rule_engine):
        data = {"x": "hello"}
        results = rule_engine.resolve_path(data, "x")
        assert results == [("/x", "hello")]

    def test_array_wildcard(self, rule_engine):
        data = {"items": [{"name": "a"}, {"name": "b"}]}
        results = rule_engine.resolve_path(data, "items[*].name")
        values = [v for _, v in results]
        assert sorted(values) == ["a", "b"]

    def test_recursive_descent(self, rule_engine):
        data = {
            "top": {
                "nested": {"measurement identifier": "uuid-1"},
                "other": {"measurement identifier": "uuid-2"},
            }
        }
        results = rule_engine.resolve_path(data, "**.measurement identifier")
        values = [v for _, v in results]
        assert "uuid-1" in values
        assert "uuid-2" in values

    def test_pipe_alternatives(self, rule_engine):
        data = {"a": {"x": 1}, "b": {"y": 2}}
        results = rule_engine.resolve_path(data, "a.x | b.y")
        values = [v for _, v in results]
        assert 1 in values
        assert 2 in values

    def test_no_match_returns_empty(self, rule_engine):
        data = {"a": 1}
        results = rule_engine.resolve_path(data, "b.c")
        assert results == []

    def test_array_in_middle_of_path(self, rule_engine):
        data = {"docs": [{"id": "A"}, {"id": "B"}]}
        results = rule_engine.resolve_path(data, "docs[*].id")
        values = [v for _, v in results]
        assert sorted(values) == ["A", "B"]


# ---------------------------------------------------------------------------
# RuleFinding
# ---------------------------------------------------------------------------

class TestRuleFinding:
    def test_to_dict(self, rule_engine):
        f = rule_engine.RuleFinding("rs1", "R-001", "L1", "error", "Bad value", "/some/path")
        d = f.to_dict()
        assert d["rule_set"] == "rs1"
        assert d["rule_id"] == "R-001"
        assert d["level"] == "L1"
        assert d["severity"] == "error"
        assert d["message"] == "Bad value"
        assert d["path"] == "/some/path"


# ---------------------------------------------------------------------------
# check_field_required
# ---------------------------------------------------------------------------

class TestCheckFieldRequired:
    def _rule(self, path, field):
        return {
            "rule_id": "FR-001", "level": "L1", "severity": "error",
            "message": "Field missing", "path": path, "field": field,
        }

    def test_field_present_no_findings(self, rule_engine):
        data = {"doc": {"sample identifier": "S001"}}
        findings = rule_engine.check_field_required(data, self._rule("doc", "sample identifier"), "rs")
        assert findings == []

    def test_field_missing_generates_finding(self, rule_engine):
        data = {"doc": {"other": "x"}}
        findings = rule_engine.check_field_required(data, self._rule("doc", "sample identifier"), "rs")
        assert len(findings) == 1

    def test_path_not_found_no_findings(self, rule_engine):
        # If the parent path doesn't exist, no finding is generated
        data = {"unrelated": 1}
        findings = rule_engine.check_field_required(data, self._rule("doc", "sample identifier"), "rs")
        assert findings == []


# ---------------------------------------------------------------------------
# check_field_not_empty
# ---------------------------------------------------------------------------

class TestCheckFieldNotEmpty:
    def _rule(self, path):
        return {
            "rule_id": "FNE-001", "level": "L1", "severity": "warning",
            "message": "Field is empty", "path": path,
        }

    def test_non_empty_no_findings(self, rule_engine):
        data = {"name": "hello"}
        findings = rule_engine.check_field_not_empty(data, self._rule("name"), "rs")
        assert findings == []

    def test_empty_string_finding(self, rule_engine):
        data = {"name": ""}
        findings = rule_engine.check_field_not_empty(data, self._rule("name"), "rs")
        assert len(findings) == 1

    def test_whitespace_only_finding(self, rule_engine):
        data = {"name": "   "}
        findings = rule_engine.check_field_not_empty(data, self._rule("name"), "rs")
        assert len(findings) == 1

    def test_non_string_ignored(self, rule_engine):
        data = {"count": 0}
        findings = rule_engine.check_field_not_empty(data, self._rule("count"), "rs")
        assert findings == []


# ---------------------------------------------------------------------------
# check_value_in_list
# ---------------------------------------------------------------------------

class TestCheckValueInList:
    def _rule(self, path, values):
        return {
            "rule_id": "VIL-001", "level": "L2", "severity": "warning",
            "message": "Unknown value: {value}", "path": path, "list_source": "_test_",
        }

    def test_valid_value_no_findings(self, rule_engine):
        data = {"role": "experiment sample role"}
        rule = {
            "rule_id": "VIL-001", "level": "L2", "severity": "warning",
            "message": "Unknown: {value}", "path": "role", "list_source": "_test_",
        }
        ref = {"_test_": ["experiment sample role", "control sample role"]}
        findings = rule_engine.check_value_in_list(data, rule, "rs", reference_data=ref)
        assert findings == []

    def test_invalid_value_finding(self, rule_engine):
        data = {"role": "made-up-role"}
        rule = {
            "rule_id": "VIL-001", "level": "L2", "severity": "warning",
            "message": "Unknown: {value}", "path": "role", "list_source": "_test_",
        }
        ref = {"_test_": ["experiment sample role"]}
        findings = rule_engine.check_value_in_list(data, rule, "rs", reference_data=ref)
        assert len(findings) == 1
        assert "made-up-role" in findings[0].message

    def test_no_list_source_no_findings(self, rule_engine):
        data = {"role": "anything"}
        rule = {
            "rule_id": "VIL-001", "level": "L2", "severity": "warning",
            "message": "Unknown: {value}", "path": "role", "list_source": "",
        }
        findings = rule_engine.check_value_in_list(data, rule, "rs")
        assert findings == []


# ---------------------------------------------------------------------------
# check_value_matches_pattern
# ---------------------------------------------------------------------------

class TestCheckValueMatchesPattern:
    def _rule(self, path, pattern):
        return {
            "rule_id": "VMP-001", "level": "L1", "severity": "error",
            "message": "Invalid value: {value}", "path": path, "pattern": pattern,
        }

    def test_uuid_valid_no_findings(self, rule_engine):
        data = {"id": "550e8400-e29b-41d4-a716-446655440000"}
        uuid_pat = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        findings = rule_engine.check_value_matches_pattern(data, self._rule("id", uuid_pat), "rs")
        assert findings == []

    def test_uuid_invalid_finding(self, rule_engine):
        data = {"id": "not-a-uuid"}
        uuid_pat = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        findings = rule_engine.check_value_matches_pattern(data, self._rule("id", uuid_pat), "rs")
        assert len(findings) == 1
        assert "not-a-uuid" in findings[0].message

    def test_iso8601_pattern(self, rule_engine):
        data = {"ts": "2024-01-15T10:30:00.000+00:00"}
        iso_pat = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        findings = rule_engine.check_value_matches_pattern(data, self._rule("ts", iso_pat), "rs")
        assert findings == []

    def test_non_string_ignored(self, rule_engine):
        data = {"count": 42}
        findings = rule_engine.check_value_matches_pattern(
            data, self._rule("count", r"^\d+$"), "rs"
        )
        assert findings == []


# ---------------------------------------------------------------------------
# check_path_exists
# ---------------------------------------------------------------------------

class TestCheckPathExists:
    def _rule(self, path):
        return {
            "rule_id": "PE-001", "level": "L3", "severity": "error",
            "message": "Path missing", "path": path,
        }

    def test_path_found_no_findings(self, rule_engine):
        data = {"device system document": {"id": "x"}}
        findings = rule_engine.check_path_exists(data, self._rule("device system document"), "rs")
        assert findings == []

    def test_path_missing_finding(self, rule_engine):
        data = {"other": 1}
        findings = rule_engine.check_path_exists(data, self._rule("device system document"), "rs")
        assert len(findings) == 1


# ---------------------------------------------------------------------------
# check_conditional_required
# ---------------------------------------------------------------------------

class TestCheckConditionalRequired:
    def test_if_path_not_present_no_findings(self, rule_engine):
        data = {"a": 1}
        rule = {
            "rule_id": "CR-001", "level": "L1", "severity": "error",
            "message": "then_path required", "if_path": "calc_data", "then_path": "data_source",
        }
        findings = rule_engine.check_conditional_required(data, rule, "rs")
        assert findings == []

    def test_if_path_present_then_path_present_no_findings(self, rule_engine):
        data = {"calc_data": {"x": 1}, "data_source": {"y": 2}}
        rule = {
            "rule_id": "CR-001", "level": "L1", "severity": "error",
            "message": "then_path required", "if_path": "calc_data", "then_path": "data_source",
        }
        findings = rule_engine.check_conditional_required(data, rule, "rs")
        assert findings == []

    def test_if_path_present_then_path_absent_finding(self, rule_engine):
        data = {"calc_data": {"x": 1}}
        rule = {
            "rule_id": "CR-001", "level": "L1", "severity": "error",
            "message": "then_path required", "if_path": "calc_data", "then_path": "data_source",
        }
        findings = rule_engine.check_conditional_required(data, rule, "rs")
        assert len(findings) == 1

    def test_if_field_variant_both_present(self, rule_engine):
        data = {"doc": {"if_key": "val", "then_key": "val2"}}
        rule = {
            "rule_id": "CR-002", "level": "L1", "severity": "error",
            "message": "then_field required", "path": "doc",
            "if_field": "if_key", "then_field": "then_key",
        }
        findings = rule_engine.check_conditional_required(data, rule, "rs")
        assert findings == []

    def test_if_field_variant_then_missing(self, rule_engine):
        data = {"doc": {"if_key": "val"}}
        rule = {
            "rule_id": "CR-002", "level": "L1", "severity": "error",
            "message": "then_field required", "path": "doc",
            "if_field": "if_key", "then_field": "then_key",
        }
        findings = rule_engine.check_conditional_required(data, rule, "rs")
        assert len(findings) == 1


# ---------------------------------------------------------------------------
# check_count_min
# ---------------------------------------------------------------------------

class TestCheckCountMin:
    def _rule(self, path, min_count):
        return {
            "rule_id": "CM-001", "level": "L1", "severity": "error",
            "message": "Too few items", "path": path, "min": min_count,
        }

    def test_array_meets_min_no_findings(self, rule_engine):
        data = {"items": [1, 2, 3]}
        findings = rule_engine.check_count_min(data, self._rule("items", 2), "rs")
        assert findings == []

    def test_array_exactly_min_no_findings(self, rule_engine):
        data = {"items": [1]}
        findings = rule_engine.check_count_min(data, self._rule("items", 1), "rs")
        assert findings == []

    def test_array_below_min_finding(self, rule_engine):
        data = {"items": []}
        findings = rule_engine.check_count_min(data, self._rule("items", 1), "rs")
        assert len(findings) == 1

    def test_non_list_ignored(self, rule_engine):
        data = {"items": "not-a-list"}
        findings = rule_engine.check_count_min(data, self._rule("items", 1), "rs")
        assert findings == []


# ---------------------------------------------------------------------------
# check_key_not_matches_pattern
# ---------------------------------------------------------------------------

class TestCheckKeyNotMatchesPattern:
    def _rule(self, pattern, exclude=None):
        return {
            "rule_id": "KNM-001", "level": "L2", "severity": "warning",
            "message": "Hyphenated key: {key}", "pattern": pattern,
            "exclude": exclude or [],
        }

    def test_clean_keys_no_findings(self, rule_engine):
        data = {"sample identifier": "x", "measurement time": "y"}
        findings = rule_engine.check_key_not_matches_pattern(
            data, self._rule(r"^[a-z]+-[a-z]+"), "rs"
        )
        assert findings == []

    def test_hyphenated_key_finding(self, rule_engine):
        data = {"sample-identifier": "x"}
        findings = rule_engine.check_key_not_matches_pattern(
            data, self._rule(r"^[a-z]+-[a-z]+"), "rs"
        )
        assert len(findings) == 1
        assert "sample-identifier" in findings[0].message

    def test_excluded_key_ignored(self, rule_engine):
        data = {"well-plate": "x"}
        findings = rule_engine.check_key_not_matches_pattern(
            data, self._rule(r"^[a-z]+-[a-z]+", exclude=["well-plate"]), "rs"
        )
        assert findings == []


# ---------------------------------------------------------------------------
# evaluate_rule_set
# ---------------------------------------------------------------------------

class TestEvaluateRuleSet:
    def test_all_pass_empty_findings(self, rule_engine, sample_valid_asm, sample_rule_set):
        findings = rule_engine.evaluate_rule_set(sample_valid_asm, sample_rule_set)
        # The valid ASM has a UUID measurement identifier, sample identifier, and device system document
        assert isinstance(findings, list)
        errors = [f for f in findings if f["severity"] == "error"]
        assert errors == []

    def test_unknown_check_type_skipped(self, rule_engine):
        data = {"x": 1}
        rule_set = {
            "rule_set_id": "test",
            "rules": [{"rule_id": "X-1", "check": "nonexistent_check_type",
                       "path": "x", "level": "L1", "severity": "error", "message": "fail"}]
        }
        findings = rule_engine.evaluate_rule_set(data, rule_set)
        assert findings == []

    def test_mixed_rules_findings(self, rule_engine):
        data = {
            "device system document": {"id": "x"},
            "measurement doc": [{"measurement identifier": "bad-id", "sample document": {}}]
        }
        rule_set = {
            "rule_set_id": "mixed",
            "rules": [
                {
                    "rule_id": "R1", "check": "path_exists",
                    "path": "device system document",
                    "level": "L1", "severity": "error", "message": "No device system doc"
                },
                {
                    "rule_id": "R2", "check": "field_required",
                    "path": "**.sample document", "field": "sample identifier",
                    "level": "L1", "severity": "error", "message": "Missing sample id"
                },
            ]
        }
        findings = rule_engine.evaluate_rule_set(data, rule_set)
        rule_ids = [f["rule_id"] for f in findings]
        # R1 should pass (path exists), R2 should fail (sample document lacks sample identifier)
        assert "R1" not in rule_ids
        assert "R2" in rule_ids

    def test_evaluate_rule_sets_aggregates(self, rule_engine):
        data = {"a": 1}
        rs1 = {"rule_set_id": "rs1", "rules": [
            {"rule_id": "A1", "check": "path_exists", "path": "missing",
             "level": "L1", "severity": "error", "message": "missing"}
        ]}
        rs2 = {"rule_set_id": "rs2", "rules": [
            {"rule_id": "B1", "check": "path_exists", "path": "also_missing",
             "level": "L1", "severity": "error", "message": "also missing"}
        ]}
        findings = rule_engine.evaluate_rule_sets(data, [rs1, rs2])
        rule_ids = {f["rule_id"] for f in findings}
        assert "A1" in rule_ids
        assert "B1" in rule_ids
